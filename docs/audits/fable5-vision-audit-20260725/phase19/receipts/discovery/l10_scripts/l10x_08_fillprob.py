import json, datetime as dt, statistics as st
from collections import Counter, defaultdict
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
OUT=f'{D}/L10X_FILLPROB_REPLACEMENT_V1.json'
OFF=10800  # MEASURED: broker epoch = true UTC + 10800 s (n=140 paired records, l10x_01)
OSTATE={0:'STARTED',1:'PLACED',2:'CANCELED',3:'PARTIAL',4:'FILLED',5:'REJECTED',6:'EXPIRED'}
def sess(h):
    if 0<=h<7: return 'asia'
    if 7<=h<12: return 'london'
    if 12<=h<17: return 'ny_overlap'
    return 'late_ny'
res={'clock_note':'broker order/deal epochs are true UTC + 10800 s (MEASURED, l10x_01_clock.py, n=140 paired lifecycle/deal records, 100% of FTMO within [10799.2,10800.7]). Every session bucket below subtracts it. The prior l10 pass bucketed on the RAW epoch and is 3 h late.'}
for acct in ['ftmo','redacted_account']:
    orders=[json.loads(l) for l in open(f'{BASE}/09_mt5_api/{acct}_history_orders_get.jsonl')]
    mk=[o for o in orders if o['type'] in (0,1)]           # market BUY/SELL only
    st_=[o for o in mk if o.get('magic')==20260401]         # strategy magic
    def tab(rows,keyf):
        d=defaultdict(lambda:[0,0])
        for o in rows:
            k=keyf(o); d[k][0]+=1
            if o['state']==4: d[k][1]+=1
        return {str(k):{'n':v[0],'filled':v[1],'fill_rate':round(v[1]/v[0],5)} for k,v in sorted(d.items(), key=lambda kv:-kv[1][0])}
    a={'n_market_orders':len(mk),'n_filled':sum(1 for o in mk if o['state']==4),
       'fill_rate':round(sum(1 for o in mk if o['state']==4)/len(mk),5),
       'n_strategy_magic':len(st_),'strategy_fill_rate':round(sum(1 for o in st_ if o['state']==4)/len(st_),5),
       'state_census':dict(Counter(OSTATE.get(o['state'],o['state']) for o in mk)),
       'by_true_utc_session':tab(mk,lambda o:sess(dt.datetime.fromtimestamp(o['time_setup']-OFF,dt.timezone.utc).hour)),
       'by_true_utc_hour':tab(mk,lambda o:dt.datetime.fromtimestamp(o['time_setup']-OFF,dt.timezone.utc).hour),
       'by_symbol':tab(mk,lambda o:o['symbol']),
       'rejected_or_canceled':[{'ticket':o['ticket'],'symbol':o['symbol'],'state':OSTATE.get(o['state']),'comment':o.get('comment'),
          'utc':dt.datetime.fromtimestamp(o['time_setup']-OFF,dt.timezone.utc).isoformat(),'magic':o.get('magic')}
          for o in mk if o['state']!=4],
       'pending_orders':[{'ticket':o['ticket'],'symbol':o['symbol'],'type':o['type'],'state':OSTATE.get(o['state']),
          'magic':o.get('magic'),'comment':o.get('comment'),
          'utc':dt.datetime.fromtimestamp(o['time_setup']-OFF,dt.timezone.utc).isoformat(),
          'sit_seconds':(o.get('time_done') or 0)-(o.get('time_setup') or 0)} for o in orders if 2<=o['type']<=7]}
    res[acct]=a
tot=res['ftmo']['n_market_orders']+res['redacted_account']['n_market_orders']
fil=res['ftmo']['n_filled']+res['redacted_account']['n_filled']
res['POOLED']={'n':tot,'filled':fil,'fill_rate':round(fil/tot,5)}
res['MODELLED_VS_REAL']={'modelled_execution_fill_probability_marketable_branch':0.92,
  'modelled_pool_mean':0.805058,'modelled_pool_min':0.0401331,
  'source':'src/components/poi_execution_lifecycle.py:174-176 (0.92) and :178-181 (distance-scaled else-branch)',
  'EMPIRICAL_REPLACEMENT_market_order':round(fil/tot,5),
  'EMPIRICAL_REPLACEMENT_limit_order':'UNMEASURABLE - src/ contains no code path that constructs a pending order (TRADE_ACTION_PENDING=5 defined at src/mt5/mt5_interface.py:63, referenced only by the activation-token classifier at src/safety/activation_token.py:625). The only entry request is src/components/execution.py:3534 action=1 TRADE_ACTION_DEAL.',
  'note':'a market order acceptance rate is NOT a limit fill probability. Substituting 0.995 for 0.92 in the research model would be a category error - the research model is pricing whether a RESTING LIMIT gets hit, an event that has never occurred in this system.'}
json.dump(res,open(OUT,'w'),indent=1)
for a in ['ftmo','redacted_account']:
    v=res[a]; print(a, 'market',v['n_market_orders'],'filled',v['n_filled'],'rate',v['fill_rate'],'| strat',v['n_strategy_magic'],v['strategy_fill_rate'],'| states',v['state_census'])
    print('   sessions(true UTC):',{k:(x['n'],x['fill_rate']) for k,x in v['by_true_utc_session'].items()})
    print('   pending:',v['pending_orders'])
    print('   not-filled:',v['rejected_or_canceled'])
print('POOLED',res['POOLED'])
