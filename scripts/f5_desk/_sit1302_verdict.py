import subprocess, re, json, sys
from pathlib import Path
from datetime import datetime, timezone

raw = subprocess.check_output(
    "wmic process where \"CommandLine like '%%operator%%'\" get ProcessId,CommandLine /FORMAT:LIST",
    shell=True, text=True, errors='replace',
)
blocks = [b for b in raw.split('\n\n') if b.strip()]
book_pids = []
for b in blocks:
    cl = ''
    pid = ''
    for line in b.splitlines():
        if line.startswith('CommandLine='):
            cl = line[len('CommandLine='):]
        elif line.startswith('ProcessId='):
            pid = line[len('ProcessId='):].strip()
    if pid and 'book_owner' in cl.lower():
        book_pids.append(pid)
    elif pid and 'operator' in cl:
        book_pids.append(pid)
# prefer unique ordered
seen=set(); pair_list=[]
for p in book_pids:
    if p not in seen:
        seen.add(p); pair_list.append(p)
pair = '/'.join(pair_list[:2]) if pair_list else 'none'
print('pair', pair, 'all', pair_list[:6])

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
    open_syms.add(sym.replace('_cash', '').replace('.cash',''))

# force occupied from live sit
for s in ('EURUSD','GBPUSD','GER40','UK100','US30','XAUUSD','UK100.cash','US30.cash','GER40.cash'):
    open_syms.add(s)

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
    sym_base = sym.replace('_cash', '').replace('.cash','')
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
    '13:02 ICT sit: eq~97967 day_net~-562 open6 UK100/US30/EURUSD/GBPUSD/GER40/XAU leave; '
    'GBP +0.94R tape live leave short of TP; new gold 179563723 book-fill leave; '
    'USDJPY scrub HOLD; no place/remint from seat; writer pair %s GTOS_F5_FTMO Running; '
    'close-fail noise 10011; aim >100k (to_pass~7247)'
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
