"""e1 step 3: is the frozen cost gate a disguised STOP-WIDTH filter?
frozen spread_r = const_px / risk_distance for 17 of 24 symbols, so 'cheap' == 'wide stop'."""
import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def m(v): return round(st.mean(v),6) if v else None
res={}
for mo in ('JAN','FEB','MAR','APR','MAY'):
    R=[]
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
        if r['opportunity_net_proxy_r'] is None: continue
        ep=r['entry_price']; sl=r['stop_loss']; spr=r['spread_r']; tc=r['expected_cost_r']
        if ep in (None,0) or sl is None or spr is None or tc is None: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        cost=r['cost_r'] if r['cost_r'] is not None else tc
        R.append({'rdp':rd/abs(ep)*100.0,'g':r['opportunity_net_proxy_r']+cost,'spr':spr,'tot':tc,
                  'pf':(spr<=0.10+1e-12 and tc<=0.15+1e-12),'sym':r['symbol'],'fam':r['origin_family']})
    R.sort(key=lambda x:x['rdp'])
    n=len(R); dec=[]
    for i in range(10):
        a,b=int(i*n/10),int((i+1)*n/10); s=R[a:b]
        dec.append({'d':i+1,'n':len(s),'rdp_lo':round(s[0]['rdp'],5),'rdp_hi':round(s[-1]['rdp'],5),
                    'gross':m([x['g'] for x in s]),'frac_pass_frozen':round(sum(1 for x in s if x['pf'])/len(s),4),
                    'median_frozen_spread_r':round(st.median([x['spr'] for x in s]),5)})
    pf=[x for x in R if x['pf']]; nf=[x for x in R if not x['pf']]
    # matched control: within each decile, compare passers vs non-passers
    R2=sorted(R,key=lambda x:x['rdp']); within=[]
    for i in range(10):
        a,b=int(i*n/10),int((i+1)*n/10); s=R2[a:b]
        p=[x['g'] for x in s if x['pf']]; q=[x['g'] for x in s if not x['pf']]
        within.append({'d':i+1,'n_pass':len(p),'n_fail':len(q),'gross_pass':m(p),'gross_fail':m(q),
                       'delta':round((st.mean(p)-st.mean(q)),6) if p and q else None})
    wp=[x for i in range(10) for x in [] ]
    tot_p=sum(x['n_pass'] for x in within); 
    wavg=round(sum(x['delta']*x['n_pass'] for x in within if x['delta'] is not None)/max(1,sum(x['n_pass'] for x in within if x['delta'] is not None)),6)
    res[mo]={'n':n,'gross_all':m([x['g'] for x in R]),'gross_pass_frozen':m([x['g'] for x in pf]),
      'gross_fail_frozen':m([x['g'] for x in nf]),'n_pass':len(pf),
      'raw_gate_edge':round(st.mean([x['g'] for x in pf])-st.mean([x['g'] for x in R]),6),
      'stopwidth_deciles':dec,'within_decile':within,
      'stopwidth_matched_gate_edge':wavg,
      'corr_rdp_vs_gross_spearman_proxy':None}
    # rank correlation rdp vs gross
    import math
    xs=list(range(n)); ys=[x['g'] for x in R]
    rk=sorted(range(n),key=lambda i:ys[i]); yr=[0]*n
    for pos,i in enumerate(rk): yr[i]=pos
    mx=(n-1)/2; sx=math.sqrt(sum((i-mx)**2 for i in xs)); sy=math.sqrt(sum((v-mx)**2 for v in yr))
    res[mo]['spearman_rdp_gross']=round(sum((xs[i]-mx)*(yr[i]-mx) for i in range(n))/(sx*sy),5)
json.dump(res,open(f'{D}/E1_STOPWIDTH_V1.json','w'),indent=1)
print(f"{'mo':<5}{'n':>7}{'grossAll':>10}{'grossPF':>10}{'grossFail':>10}{'rawEdge':>9}{'matchedEdge':>12}{'spearman':>10}")
for mo,v in res.items():
    print(f"{mo:<5}{v['n']:>7}{v['gross_all']:>10.4f}{v['gross_pass_frozen']:>10.4f}{v['gross_fail_frozen']:>10.4f}{v['raw_gate_edge']:>9.4f}{v['stopwidth_matched_gate_edge']:>12.4f}{v['spearman_rdp_gross']:>10.4f}")
print()
print('JAN stop-width deciles (risk distance as % of price):')
print(f"{'d':>3}{'n':>7}{'rdp_lo':>9}{'rdp_hi':>9}{'gross':>9}{'fracPassFrozen':>16}{'medSprR':>9}")
for d in res['JAN']['stopwidth_deciles']:
    print(f"{d['d']:>3}{d['n']:>7}{d['rdp_lo']:>9.4f}{d['rdp_hi']:>9.4f}{d['gross']:>9.4f}{d['frac_pass_frozen']:>16.4f}{d['median_frozen_spread_r']:>9.4f}")
