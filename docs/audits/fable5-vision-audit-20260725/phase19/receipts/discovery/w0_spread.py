import gzip, json, sys, collections, statistics
from datetime import datetime
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from src.costs.spread_model import spread_price
P='docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'
rows=[json.loads(l) for l in gzip.open(P,'rt')]
cache={}
def sp(sym,iso):
    dt=datetime.fromisoformat(iso); k=(sym,dt.strftime('%Y-%m-%dT%H'))
    if k not in cache: cache[k]=spread_price(sym,'FTMO',dt,band='mid').spread_price
    return cache[k]
ratios=[]; per_sym=collections.defaultdict(list)
tot_frozen=0.0; tot_true=0.0
for r in rows:
    d=abs(r['entry_price']-r['stop_loss'])
    st=sp(r['symbol'], r['decision_time_utc'])
    true_r=st/d
    ratios.append((r['spread_r'], true_r, r['symbol']))
    per_sym[r['symbol']].append((r['spread_r'], true_r))
    tot_frozen+=r['spread_r']; tot_true+=true_r
n=len(rows)
print('mean frozen spread_r %.6f  mean truthed spread_r %.6f  ratio %.4fx'%(tot_frozen/n, tot_true/n, (tot_frozen/n)/(tot_true/n)))
rr=[a/b for a,b,_ in ratios if b>0]
rr.sort()
print('per-row ratio frozen/true: p05 %.3f med %.3f mean %.3f p95 %.3f'%(rr[int(.05*n)],rr[n//2],sum(rr)/len(rr),rr[int(.95*n)]))
print('%-12s %8s %10s %10s %8s'%('symbol','n','frozen','true','ratio'))
out={}
for s,v in sorted(per_sym.items(), key=lambda x:-len(x[1])):
    f=sum(a for a,b in v)/len(v); t=sum(b for a,b in v)/len(v)
    print('%-12s %8d %10.5f %10.5f %8.2f'%(s,len(v),f,t,f/t))
    out[s]={'n':len(v),'mean_frozen_spread_r':f,'mean_true_spread_r':t,'ratio':f/t}
# cost recomputation
mc_f=sum(r['cost_r'] for r in rows)/n
mc_t=sum((r['commission_r']+r['swap_cost_r']+0.02+ sp(r['symbol'],r['decision_time_utc'])/abs(r['entry_price']-r['stop_loss'])) for r in rows)/n
print('mean cost_r frozen %.5f -> truthed %.5f (ratio %.3fx, delta %.5f R/trade)'%(mc_f,mc_t,mc_f/mc_t,mc_f-mc_t))
json.dump({'mean_frozen_spread_r':tot_frozen/n,'mean_true_spread_r':tot_true/n,'overcharge_x':(tot_frozen/n)/(tot_true/n),
 'mean_cost_frozen':mc_f,'mean_cost_true':mc_t,'per_symbol':out,'n':n}, open('/tmp/w0_spread.json','w'), indent=1)
