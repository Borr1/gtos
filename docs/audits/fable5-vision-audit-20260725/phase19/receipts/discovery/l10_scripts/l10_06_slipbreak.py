import json, datetime as dt
from collections import Counter, defaultdict
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
R=json.load(open(OUTD+'/L10_SLIP_RECORDS_V1.json'))
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p90=round(q(v,.9),r),max=round(max(v),r),min=round(min(v),r))
out={}
# per symbol
per=defaultdict(list)
for x in R: per[x['sym']].append(x)
tbl={}
for s,g in sorted(per.items(), key=lambda kv:-len(kv[1])):
    sl=[x['slip_r'] for x in g if x['slip_r'] is not None]
    tbl[s]=dict(n=len(g), slip_r=S(sl), zero=sum(1 for v in sl if abs(v)<1e-12),
                adverse=sum(1 for v in sl if v>1e-12), fav=sum(1 for v in sl if v<-1e-12),
                slip_price=S([x['slip_price'] for x in g]),
                model_spread_r=S([x['m_spread_r'] for x in g]),
                model_total_cost_r=S([x['m_total_cost_r'] for x in g]),
                mean_deviation_points=S([x['dev'] for x in g],2))
out['per_symbol']=tbl
# per hour UTC
ph=defaultdict(list)
for x in R:
    h=dt.datetime.fromisoformat(x['t']).hour; ph[h].append(x['slip_r'])
out['per_hour_utc']={str(h):S(v) for h,v in sorted(ph.items())}
# per side
out['per_side']={sd:S([x['slip_r'] for x in R if x['side']==sd]) for sd in ('LONG','SHORT')}
# by asset class
def cls(s):
    if s in ('BTCUSD','ETHUSD','AVAUSD','DASHUSD'): return 'crypto'
    if 'XAU' in s or 'XAG' in s: return 'metals'
    if 'OIL' in s or 'NATGAS' in s: return 'energy'
    if any(k in s for k in ('GER','JP225','UK100','US30','US100','US500','SPX','NDX','NAS','AUS200','EU50','SPN35')): return 'index'
    return 'fx'
pc=defaultdict(list)
for x in R: pc[cls(x['sym'])].append(x)
out['per_class']={c:dict(n=len(g),slip_r=S([x['slip_r'] for x in g]),
                          model_spread_r=S([x['m_spread_r'] for x in g]),
                          model_total_cost_r=S([x['m_total_cost_r'] for x in g]),
                          zero=sum(1 for x in g if x['slip_r'] is not None and abs(x['slip_r'])<1e-12))
                  for c,g in sorted(pc.items())}
# deviation parameter used
out['deviation_points']=dict(Counter(x['dev'] for x in R).most_common(20))
out['slip_r_vs_model_flat_0p02']=dict(
    real_mean=round(sum(x['slip_r'] for x in R if x['slip_r'] is not None)/len(R),6),
    model_flat=0.02,
    overcharge_ratio_mean=round(0.02/ (sum(x['slip_r'] for x in R if x['slip_r'] is not None)/len(R)),4),
    n_fills_where_model_over=sum(1 for x in R if x['slip_r'] is not None and x['slip_r']<0.02),
    n_fills_where_model_under=sum(1 for x in R if x['slip_r'] is not None and x['slip_r']>0.02),
    frac_model_over=round(sum(1 for x in R if x['slip_r'] is not None and x['slip_r']<0.02)/len(R),4))
json.dump(out,open(OUTD+'/L10_SLIP_BREAKDOWN_V1.json','w'),indent=1)
print('CLASS:'); 
for c,v in out['per_class'].items(): print('  ',c,'n',v['n'],'slipR',v['slip_r'],'zero',v['zero'])
print('SIDE:',out['per_side'])
print('DEV:',out['deviation_points'])
print('VS FLAT:',out['slip_r_vs_model_flat_0p02'])
print('TOP SYMBOLS:')
for s,v in list(tbl.items())[:10]: print('  ',s,'n',v['n'],'slipR mean',v['slip_r']['mean'],'med',v['slip_r']['median'],'zero',v['zero'],'adv',v['adverse'],'fav',v['fav'])
