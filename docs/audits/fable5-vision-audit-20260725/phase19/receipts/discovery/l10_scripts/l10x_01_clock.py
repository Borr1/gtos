import json, datetime as dt, statistics as st
from collections import Counter
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted'
OUT='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L10X_CLOCK_V1.json'
rows=[json.loads(l) for l in open(f'{BASE}/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl')]
ex=[r for r in rows if r.get('stage')=='entry_fill_reconciled']
deals={}
for acct in ['ftmo','redacted_account']:
    for l in open(f'{BASE}/09_mt5_api/{acct}_history_deals_get.jsonl'):
        d=json.loads(l); deals[(acct,d['ticket'])]=d
res={'method':'lifecycle entry_fill_reconciled runtime order_send_time_utc (python datetime.now(utc) on the VPS) vs raw MT5 deal time epoch joined by deal_ticket'}
off={'ftmo':[],'redacted_account':[],'unknown':[]}
matched=0; unmatched=0
for r in ex:
    dc=r.get('deal_cost_reconciliation') or {}
    dt_tk=dc.get('deal_ticket')
    ost=(r.get('order_send_observation') or {}).get('order_send_time_utc')
    if not dt_tk or not ost: continue
    hit=None; acct=None
    for a in ['ftmo','redacted_account']:
        if (a,dt_tk) in deals: hit=deals[(a,dt_tk)]; acct=a; break
    if hit is None: unmatched+=1; continue
    matched+=1
    t_send=dt.datetime.fromisoformat(ost).timestamp()
    off[acct].append(hit['time']-t_send)
res['matched']=matched; res['unmatched']=unmatched
for a in ['ftmo','redacted_account']:
    v=off[a]
    if v:
        res[a]={'n':len(v),'mean_s':round(st.mean(v),3),'median_s':round(st.median(v),3),
                'min_s':round(min(v),3),'max_s':round(max(v),3),
                'frac_within_2s':round(sum(1 for x in v if abs(x)<=2)/len(v),4),
                'frac_near_10800':round(sum(1 for x in v if 10790<=x<=10810)/len(v),4)}
# coverage windows in the SAME convention as the runtime clock
def iso(ts): return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()
cov={}
for acct in ['ftmo','redacted_account']:
    o=[json.loads(l) for l in open(f'{BASE}/09_mt5_api/{acct}_history_orders_get.jsonl')]
    d=[json.loads(l) for l in open(f'{BASE}/09_mt5_api/{acct}_history_deals_get.jsonl')]
    ts=[x['time_setup'] for x in o if x.get('time_setup')]
    td=[x['time'] for x in d if x.get('time')]
    strat=[x for x in o if x.get('magic')==20260401]
    tstr=[x['time_setup'] for x in strat if x.get('time_setup')]
    cov[acct]={'n_orders':len(o),'n_deals':len(d),
        'orders_window':[iso(min(ts)),iso(max(ts))],'deals_window':[iso(min(td)),iso(max(td))],
        'n_strategy_magic_orders':len(strat),
        'strategy_window':[iso(min(tstr)),iso(max(tstr))] if tstr else None,
        'magic_counts':dict(Counter(x.get('magic') for x in o)),
        'trading_days':len({iso(x)[:10] for x in ts})}
res['coverage']=cov
res['post_arming_2026_07_29_records']={a:sum(1 for x in json.load(open('/dev/null')) ) if False else 0 for a in ['ftmo','redacted_account']}
# explicit: count any order/deal at/after 2026-07-29
cut=dt.datetime(2026,7,29,tzinfo=dt.timezone.utc).timestamp()
pa={}
for acct in ['ftmo','redacted_account']:
    o=[json.loads(l) for l in open(f'{BASE}/09_mt5_api/{acct}_history_orders_get.jsonl')]
    d=[json.loads(l) for l in open(f'{BASE}/09_mt5_api/{acct}_history_deals_get.jsonl')]
    pa[acct]={'orders_on_or_after_20260729':sum(1 for x in o if (x.get('time_setup') or 0)>=cut),
              'deals_on_or_after_20260729':sum(1 for x in d if (x.get('time') or 0)>=cut)}
res['post_arming_2026_07_29_records']=pa
json.dump(res,open(OUT,'w'),indent=1)
print(json.dumps({k:v for k,v in res.items() if k!='coverage'},indent=1)[:1600])
print('--- coverage ---')
for a,v in cov.items(): print(a, v['n_orders'],'orders',v['n_deals'],'deals', v['orders_window'], 'strat',v['n_strategy_magic_orders'], v['strategy_window'], 'days',v['trading_days'])
