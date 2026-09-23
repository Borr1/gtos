import json,os,statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
A=json.load(open(f'{D}/E2_MONTHS_ANCHORED_V1.json'))
MO=['JAN','FEB','APR','MAY']
def rank_corr(a,b):
    # Spearman over common keys
    ks=[k for k in a if k in b]
    if len(ks)<3: return None
    ra={k:i for i,k in enumerate(sorted(ks,key=lambda k:a[k]))}
    rb={k:i for i,k in enumerate(sorted(ks,key=lambda k:b[k]))}
    n=len(ks); d2=sum((ra[k]-rb[k])**2 for k in ks)
    return round(1-6*d2/(n*(n*n-1)),4)
out={'months':MO}
for dim,fld in [('per_family_takeable','real_cost'),('per_symbol_takeable','real_cost'),
                ('per_family_takeable','net_real'),('per_symbol_takeable','net_real'),
                ('per_family_takeable','gross'),('per_symbol_takeable','gross')]:
    tab={}
    for mo in MO:
        tab[mo]={k:v[fld] for k,v in A[mo][dim].items() if v[fld] is not None}
    keys=sorted(set.intersection(*[set(tab[m]) for m in MO]))
    rows={k:{m:tab[m].get(k) for m in MO} for k in keys}
    for k in rows:
        vs=[rows[k][m] for m in MO if rows[k][m] is not None]
        rows[k]['mean']=round(st.mean(vs),6); rows[k]['min']=round(min(vs),6); rows[k]['max']=round(max(vs),6)
        rows[k]['n_by_mo']={m:A[mo][dim].get(k,{}).get('n') for mo,m in [(m,m) for m in MO]}
        rows[k]['n_by_mo']={m:A[m][dim].get(k,{}).get('n') for m in MO}
        rows[k]['sign_consistent_negative']=all(v<0 for v in vs)
        rows[k]['sign_consistent_positive']=all(v>0 for v in vs)
    corrs={}
    for i in range(len(MO)):
        for j in range(i+1,len(MO)):
            corrs[f'{MO[i]}~{MO[j]}']=rank_corr(tab[MO[i]],tab[MO[j]])
    out[f'{dim}__{fld}']={'rows':rows,'spearman':corrs,'n_common':len(keys),
        'mean_spearman':round(st.mean([v for v in corrs.values() if v is not None]),4)}
json.dump(out,open(f'{D}/E2_BOUNDARY_V1.json','w'),indent=1)
def show(key,lbl,w=34):
    o=out[key]; print(f'--- {lbl}   mean Spearman across the 6 month-pairs = {o["mean_spearman"]}')
    print(f"{'key':<{w}}"+''.join(f'{m:>10}' for m in MO)+f"{'mean':>10}")
    for k,v in sorted(o['rows'].items(),key=lambda kv:kv[1]['mean']):
        print(f"{k:<{w}}"+''.join(f"{v[m]:>10.4f}" if v[m] is not None else f"{'-':>10}" for m in MO)+f"{v['mean']:>10.4f}")
show('per_family_takeable__real_cost','FAMILY REAL COST R/trade (takeable)')
print()
show('per_family_takeable__net_real','FAMILY NET @ REAL COST (takeable)')
print()
show('per_family_takeable__gross','FAMILY GROSS (takeable)')
