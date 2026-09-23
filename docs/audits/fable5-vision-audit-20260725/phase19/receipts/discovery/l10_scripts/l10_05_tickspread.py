import json, gzip, os, sys, datetime as dt
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from src.utils.broker_clock import resolve_rule, broker_epoch_to_utc
from collections import defaultdict
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
TICK='/Users/borr/GTOSActive/vps-ticks-20260726'
R=json.load(open(OUTD+'/L10_SLIP_RECORDS_V1.json'))
# --- account attribution by deal ticket membership
tick_sets={}
for a in ['ftmo','redacted_account']:
    tick_sets[a]=set(json.loads(l)['ticket'] for l in open(f'{BASE}/{a}_history_deals_get.jsonl'))
for r in R:
    dt_=r.get('comm') # placeholder
    t=r.get('deal_ticket') if 'deal_ticket' in r else None
r2=[]
raw=json.load(open(OUTD+'/L10_ENTRY_FILLS_RAW_V1.json'))
by_cid={}
for x in raw:
    by_cid[(x['candidate_id'],x['decision_time_utc'])]=x
for r in R:
    x=by_cid.get((r['cid'],r['t']))
    dtk=x.get('deal_ticket') if x else None
    acct=None
    for a,s in tick_sets.items():
        if dtk in s: acct=a; break
    r['deal_ticket']=dtk; r['acct']=acct
    r2.append(r)
R=r2
from collections import Counter
print('acct attribution:',Counter(r['acct'] for r in R))
RULES={'ftmo':resolve_rule('FTMO-Server3'),'redacted_account':resolve_rule('redacted_account-Server 2')}
def tickfile(acct,sym):
    s=sym.replace('.','_')
    if acct=='ftmo': p=f'{TICK}/ftmo/FTMO_{s}_ticks_20260618_to_20260726.csv.gz'
    else: p=f'{TICK}/redacted_account/redacted_account_{s}_ticks_20260618_to_20260726.csv.gz'
    return p if os.path.isfile(p) else None
groups=defaultdict(list)
for i,r in enumerate(R):
    if r['acct']: groups[(r['acct'],r['sym'])].append(i)
print('groups',len(groups))
missing=[]
res={}
for (acct,sym),idxs in sorted(groups.items()):
    p=tickfile(acct,sym)
    if not p:
        missing.append(f'{acct}:{sym}({len(idxs)})'); continue
    rule=RULES[acct]
    targets=sorted([(dt.datetime.fromisoformat(R[i]['t']).timestamp(), i) for i in idxs])
    # stream ticks, keep best tick <= target and first tick >= target
    best={i:{'before':None,'after':None} for _,i in targets}
    ti=0
    with gzip.open(p,'rt') as fh:
        hdr=fh.readline().strip().split(',')
        ix={c:k for k,c in enumerate(hdr)}
        cb,ca,ct=ix.get('bid'),ix.get('ask'),ix.get('time_msc') if 'time_msc' in ix else ix.get('time')
        use_msc='time_msc' in ix
        for line in fh:
            f=line.rstrip('\n').split(',')
            try:
                be=(float(f[ct])/1000.0) if use_msc else float(f[ct])
            except Exception: continue
            ts=broker_epoch_to_utc(be, rule).timestamp()
            while ti<len(targets) and ts>targets[ti][0]:
                # first tick strictly after target
                i=targets[ti][1]
                if best[i]['after'] is None:
                    try: best[i]['after']=(ts,float(f[cb]),float(f[ca]))
                    except Exception: pass
                ti+=1
            # record 'before' for all remaining targets whose time >= ts
            for k in range(ti,len(targets)):
                if targets[k][0]>=ts:
                    i=targets[k][1]
                    try: best[i]['before']=(ts,float(f[cb]),float(f[ca]))
                    except Exception: pass
                else: break
    for i in idxs:
        b=best[i]['before']; a2=best[i]['after']
        pick=b if b else a2
        if pick:
            R[i]['real_bid']=pick[1]; R[i]['real_ask']=pick[2]
            R[i]['real_spread_price']=round(pick[2]-pick[1],10)
            R[i]['tick_age_s']=round(dt.datetime.fromisoformat(R[i]['t']).timestamp()-pick[0],3)
            R[i]['tick_side']='before' if b else 'after'
    res[f'{acct}:{sym}']=sum(1 for i in idxs if 'real_spread_price' in R[i])
print('missing tick files:',missing)
print('matched per group:',res)
json.dump(R,open(OUTD+'/L10_SLIP_WITH_REAL_SPREAD_V1.json','w'),indent=0)
print('DONE rows_with_real_spread=',sum(1 for r in R if 'real_spread_price' in r),'of',len(R))
