"""Is the frozen cost model a SCALE error (uniformly ~3.5x, gate merely too tight) or a
RANKING error (gate refuses the wrong candidates)?  Row-level Spearman frozen vs real,
plus the confusion matrix of the two gates, per month."""
import json,sys,os,statistics as st
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
D=E.D
JOBS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_JAN.jsonl.gz'),
      ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_FEB.jsonl.gz'),
      ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_APR.jsonl.gz'),
      ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAY.jsonl.gz')]
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
out={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False)
    tk=[x for x in rows if x['bs']!='born_past_stop']
    fz=[x['froz_tot'] for x in rows]; rl=[x['rtot'] for x in rows]
    fzs=[x['froz_spr'] for x in rows]; rls=[x['rspr'] for x in rows]
    # per-row ratio (guard zero)
    rat=[x['froz_tot']/x['rtot'] for x in rows if x['rtot']>1e-12]
    # gate confusion on ALL rows
    gf=[E.gate(x['froz_spr'],x['froz_tot']) for x in rows]
    gr=[E.gate(x['rspr'],x['rtot']) for x in rows]
    both=sum(1 for a_,b_ in zip(gf,gr) if a_ and b_)
    fonly=sum(1 for a_,b_ in zip(gf,gr) if a_ and not b_)
    ronly=sum(1 for a_,b_ in zip(gf,gr) if b_ and not a_)
    neither=sum(1 for a_,b_ in zip(gf,gr) if not a_ and not b_)
    def gm(sel): 
        v=[x['gross'] for x,s in zip(rows,sel) if s]; return round(st.mean(v),6) if v else None
    def nm(sel):
        v=[x['gross']-x['rtot'] for x,s in zip(rows,sel) if s]; return round(st.mean(v),6) if v else None
    sel_fonly=[a_ and not b_ for a_,b_ in zip(gf,gr)]
    sel_ronly=[b_ and not a_ for a_,b_ in zip(gf,gr)]
    sel_both=[a_ and b_ for a_,b_ in zip(gf,gr)]
    # per-family frozen/real ratio
    from collections import defaultdict
    pf=defaultdict(list)
    for x in tk: pf[x['fam']].append(x)
    famrat={k:round(st.mean([y['froz_tot'] for y in v])/st.mean([y['rtot'] for y in v]),4) for k,v in pf.items()}
    ps=defaultdict(list)
    for x in tk: ps[x['sym']].append(x)
    symrat={k:round(st.mean([y['froz_tot'] for y in v])/st.mean([y['rtot'] for y in v]),4) for k,v in ps.items()}
    out[lbl]={'n':len(rows),
      'spearman_frozen_vs_real_total':spearman(fz,rl),
      'spearman_frozen_vs_real_spread':spearman(fzs,rls),
      'row_ratio_frozen_over_real':{'mean':round(st.mean(rat),4),'median':round(st.median(rat),4),
         'p10':round(sorted(rat)[len(rat)//10],4),'p90':round(sorted(rat)[9*len(rat)//10],4),
         'p01':round(sorted(rat)[len(rat)//100],4),'p99':round(sorted(rat)[99*len(rat)//100],4),
         'iqr_ratio':round(sorted(rat)[3*len(rat)//4]/sorted(rat)[len(rat)//4],4)},
      'GATE_CONFUSION':{'both':both,'frozen_only':fonly,'real_only':ronly,'neither':neither,
         'disagreement_rate':round((fonly+ronly)/len(rows),5),
         'gross_of_both':gm(sel_both),'gross_of_frozen_only':gm(sel_fonly),'gross_of_real_only':gm(sel_ronly),
         'netreal_of_both':nm(sel_both),'netreal_of_frozen_only':nm(sel_fonly),'netreal_of_real_only':nm(sel_ronly)},
      'family_ratio':dict(sorted(famrat.items(),key=lambda kv:kv[1])),
      'symbol_ratio':dict(sorted(symrat.items(),key=lambda kv:kv[1])),
      'family_ratio_spread':round(max(famrat.values())/min(famrat.values()),3),
      'symbol_ratio_spread':round(max(symrat.values())/min(symrat.values()),3)}
json.dump(out,open(f'{D}/E2_SCALE_VS_RANK_V1.json','w'),indent=1)
print(f"{'mo':<5}{'rhoTotal':>10}{'rhoSpread':>11}{'ratMed':>8}{'ratP10':>8}{'ratP90':>8}{'IQRrat':>8}{'famSpr':>8}{'symSpr':>8}")
for k,v in out.items():
    r=v['row_ratio_frozen_over_real']
    print(f"{k:<5}{v['spearman_frozen_vs_real_total']:>10.4f}{v['spearman_frozen_vs_real_spread']:>11.4f}{r['median']:>8.2f}{r['p10']:>8.2f}{r['p90']:>8.2f}{r['iqr_ratio']:>8.2f}{v['family_ratio_spread']:>8.2f}{v['symbol_ratio_spread']:>8.2f}")
print()
print(f"{'mo':<5}{'both':>7}{'frozOnly':>9}{'realOnly':>9}{'neither':>8}{'disag':>8}{'grBoth':>9}{'grFonly':>9}{'grRonly':>9}{'nrRonly':>9}")
for k,v in out.items():
    c=v['GATE_CONFUSION']
    print(f"{k:<5}{c['both']:>7}{c['frozen_only']:>9}{c['real_only']:>9}{c['neither']:>8}{c['disagreement_rate']:>8.3f}{c['gross_of_both']:>9.4f}{(c['gross_of_frozen_only'] if c['gross_of_frozen_only'] is not None else 0):>9.4f}{c['gross_of_real_only']:>9.4f}{c['netreal_of_real_only']:>9.4f}")
