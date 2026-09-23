import json, collections, datetime as dt, statistics as st
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
specs={}
for b in ('ftmo','redacted_account'):
    s=json.load(open(E+f'{b}_symbol_specs_traded.json'))
    specs[b]={k:v for k,v in s.items()}
print('spec fields sample', {k:specs['ftmo']['AUDJPY'].get(k) for k in ('trade_contract_size','trade_tick_value','trade_tick_size','point','currency_profit','currency_base','swap_mode','swap_rollover3days','swap_long','swap_short','digits')})
out={}
for b in ('ftmo','redacted_account'):
    deals=[json.loads(l) for l in open(E+f'{b}_history_deals_get.jsonl')]
    tt=collections.Counter(d['type'] for d in deals)
    ee=collections.Counter(d['entry'] for d in deals)
    print(b,'deals',len(deals),'types',dict(tt),'entry',dict(ee))
    syms=collections.Counter(d['symbol'] for d in deals if d['symbol'])
    print(' symbols', len(syms), syms.most_common(8))
    mg=collections.Counter(d['magic'] for d in deals)
    print(' magics', mg.most_common())
    ts=[d['time'] for d in deals if d['symbol']]
    print(' range', dt.datetime.utcfromtimestamp(min(ts)).isoformat(), dt.datetime.utcfromtimestamp(max(ts)).isoformat())
    out[b]=deals
json.dump({k:len(v) for k,v in out.items()}, open('/tmp/h4/_deals_count.json','w'))
