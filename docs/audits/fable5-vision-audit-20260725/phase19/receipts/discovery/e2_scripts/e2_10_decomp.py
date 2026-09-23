"""Decompose the lever (cost saved vs better trades selected), extend scale-vs-rank to MARCH,
and measure the symbol / session / hour boundary across all five months."""
import json,sys,os,statistics as st
from collections import defaultdict
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
D=E.D
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
JOBS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_JAN.jsonl.gz'),
      ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_FEB.jsonl.gz'),
      ('MAR',f'{D}/e2_MARCH_R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAR.jsonl.gz'),
      ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_APR.jsonl.gz'),
      ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAY.jsonl.gz')]
ALL={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False); ALL[lbl]=rows
MO=list(ALL)
def spearman(xs,ys):
    n=len(xs)
    def rk(v):
        o=sorted(range(n),key=lambda i:v[i]); r=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and v[o[j+1]]==v[o[i]]: j+=1
            avg=(i+j)/2.0
            for k in range(i,j+1): r[o[k]]=avg
            i=j+1
        return r
    rx,ry=rk(xs),rk(ys); mx,my=st.mean(rx),st.mean(ry)
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den=(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**0.5
    return round(num/den,6) if den else None
out={'months':MO}
# --- 1. lever decomposition, staged
JF=['regime_transition_break','volatility_compression_expansion','session_open_range_break','displacement_continuation']
stages={}
for mo in MO:
    rows=ALL[mo]; tk=[x for x in rows if x['bs']!='born_past_stop']
    js=None
    def bk(rr): 
        return {'n':len(rr),'gross':E.m_([x['gross'] for x in rr]),'real_cost':E.m_([x['rtot'] for x in rr]),
                'net_real':E.m_([x['gross']-x['rtot'] for x in rr])} if rr else {'n':0}
    s={}
    s['S0_all']=bk(rows)
    s['S1_takeable']=bk(tk)
    s['S2_takeable_4fam']=bk([x for x in tk if x['fam'] in JF])
    s['S3_takeable_4fam_12sym']=None
    stages[mo]=s
# 12 cheapest symbols chosen on JANUARY
jt=[x for x in ALL['JAN'] if x['bs']!='born_past_stop']
bysym=defaultdict(list)
for x in jt: bysym[x['sym']].append(x)
SR=sorted(bysym,key=lambda k:st.mean([y['rtot'] for y in bysym[k]]))[:12]
for mo in MO:
    tk=[x for x in ALL[mo] if x['bs']!='born_past_stop']
    c1=[x for x in tk if x['fam'] in JF and x['sym'] in SR]
    c2=[x for x in c1 if E.gate(x['rspr'],x['rtot'])]
    def bk(rr):
        return {'n':len(rr),'gross':E.m_([x['gross'] for x in rr]),'real_cost':E.m_([x['rtot'] for x in rr]),
                'net_real':E.m_([x['gross']-x['rtot'] for x in rr])} if rr else {'n':0}
    stages[mo]['S3_takeable_4fam_12sym']=bk(c1)
    stages[mo]['S4_plus_realgate']=bk(c2)
out['LEVER_STAGES']=stages; out['JAN_SELECTED_4_FAMILIES']=JF; out['JAN_SELECTED_12_SYMBOLS']=SR
# --- 2. scale-vs-rank, all five
sr={}
for mo in MO:
    rows=ALL[mo]
    fz=[x['froz_tot'] for x in rows]; rl=[x['rtot'] for x in rows]
    gf=[E.gate(x['froz_spr'],x['froz_tot']) for x in rows]; gr=[E.gate(x['rspr'],x['rtot']) for x in rows]
    both=sum(1 for a,b in zip(gf,gr) if a and b); fo=sum(1 for a,b in zip(gf,gr) if a and not b)
    ro=sum(1 for a,b in zip(gf,gr) if b and not a); ne=sum(1 for a,b in zip(gf,gr) if not a and not b)
    def st_(sel,fld):
        v=[(x['gross'] if fld=='g' else x['gross']-x['rtot']) for x,s in zip(rows,sel) if s]
        return round(st.mean(v),6) if v else None
    sel_b=[a and b for a,b in zip(gf,gr)]; sel_f=[a and not b for a,b in zip(gf,gr)]; sel_r=[b and not a for a,b in zip(gf,gr)]
    rat=[x['froz_tot']/x['rtot'] for x in rows if x['rtot']>1e-12]; rs=sorted(rat)
    tkr=[x for x in rows if x['bs']!='born_past_stop']
    ps=defaultdict(list); pfm=defaultdict(list)
    for x in tkr: ps[x['sym']].append(x); pfm[x['fam']].append(x)
    symrat={k:round(st.mean([y['froz_tot'] for y in v])/st.mean([y['rtot'] for y in v]),4) for k,v in ps.items()}
    famrat={k:round(st.mean([y['froz_tot'] for y in v])/st.mean([y['rtot'] for y in v]),4) for k,v in pfm.items()}
    sr[mo]={'n':len(rows),'spearman_frozen_vs_real':spearman(fz,rl),
      'row_ratio_median':round(rs[len(rs)//2],4),'row_ratio_p10':round(rs[len(rs)//10],4),
      'row_ratio_p90':round(rs[9*len(rs)//10],4),
      'gate_both':both,'gate_frozen_only':fo,'gate_real_only':ro,'gate_neither':ne,
      'disagreement_rate':round((fo+ro)/len(rows),5),
      'gross_both':st_(sel_b,'g'),'gross_frozen_only':st_(sel_f,'g'),'gross_real_only':st_(sel_r,'g'),
      'netreal_both':st_(sel_b,'n'),'netreal_frozen_only':st_(sel_f,'n'),'netreal_real_only':st_(sel_r,'n'),
      'symbol_ratio_min':min(symrat.values()),'symbol_ratio_max':max(symrat.values()),
      'symbol_ratio_spread':round(max(symrat.values())/min(symrat.values()),3),
      'family_ratio_spread':round(max(famrat.values())/min(famrat.values()),3),
      'symbol_ratio':dict(sorted(symrat.items(),key=lambda kv:kv[1])),
      'family_ratio':dict(sorted(famrat.items(),key=lambda kv:kv[1]))}
out['SCALE_VS_RANK']=sr
# --- 3. symbol / session boundary, takeable
def grp(mo,key):
    g=defaultdict(list)
    for x in ALL[mo]:
        if x['bs']=='born_past_stop': continue
        g[x[key]].append(x)
    return {str(k):{'n':len(v),'gross':E.m_([y['gross'] for y in v]),'real_cost':E.m_([y['rtot'] for y in v]),
                    'net_real':E.m_([y['gross']-y['rtot'] for y in v])} for k,v in g.items()}
for key,nm in [('sym','SYMBOL'),('sess','SESSION')]:
    tab={mo:grp(mo,key) for mo in MO}
    keys=sorted(set.intersection(*[set(tab[m]) for m in MO]))
    rows={}
    for k in keys:
        gs=[tab[m][k]['gross'] for m in MO]; ns=[tab[m][k]['n'] for m in MO]; nr=[tab[m][k]['net_real'] for m in MO]
        rows[k]={'n_by_month':dict(zip(MO,ns)),'gross_by_month':dict(zip(MO,gs)),'net_real_by_month':dict(zip(MO,nr)),
                 'gross_mean':round(st.mean(gs),6),'net_real_mean':round(st.mean(nr),6),
                 'real_cost_mean':round(st.mean([tab[m][k]['real_cost'] for m in MO]),6),
                 'months_gross_positive':sum(1 for g in gs if g>0),'n_total':sum(ns)}
    out[f'BOUNDARY_{nm}']={'rows':rows,'n_common':len(keys)}
json.dump(out,open(f'{D}/E2_DECOMP_V1.json','w'),indent=1)
print('=== LEVER STAGES: net@real (n) ===')
print(f"{'stage':<26}"+''.join(f'{m:>18}' for m in MO))
for s in ['S0_all','S1_takeable','S2_takeable_4fam','S3_takeable_4fam_12sym','S4_plus_realgate']:
    print(f"{s:<26}"+''.join(f"{stages[m][s]['net_real']:>11.4f}({stages[m][s]['n']:>5})" for m in MO))
print(f"{'  of which GROSS':<26}"+''.join(f"{stages[m]['S4_plus_realgate']['gross']:>18.4f}" for m in MO))
print()
print('=== SCALE vs RANK (five months) ===')
print(f"{'mo':<5}{'rho':>8}{'ratMed':>8}{'disagree':>10}{'frozOnly':>9}{'realOnly':>9}{'symRatSpr':>10}{'famRatSpr':>10}")
for m in MO:
    v=sr[m]; print(f"{m:<5}{v['spearman_frozen_vs_real']:>8.4f}{v['row_ratio_median']:>8.2f}{v['disagreement_rate']:>10.3f}{v['gate_frozen_only']:>9}{v['gate_real_only']:>9}{v['symbol_ratio_spread']:>10.1f}{v['family_ratio_spread']:>10.2f}")
