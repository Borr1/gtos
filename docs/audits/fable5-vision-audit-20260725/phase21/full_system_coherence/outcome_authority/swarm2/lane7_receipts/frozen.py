import json, pandas as pd, numpy as np
B='/Users/borr/GTOSActive/worktrees/three-sleeve-restatement-20260811/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/'
recs=[]
for f,tag in [('FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json','feb'),
              ('APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json','aprmay'),
              ('JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json','junjul')]:
    d=json.load(open(B+f))
    for r in d['selected_candidates']:
        r=dict(r); r['window']=tag; recs.append(r)
df=pd.DataFrame(recs)
df['month']=pd.to_datetime(df.trading_day).dt.strftime('%Y-%m')
df['hour']=df.utc_session.str.extract(r'moonshot_h(\d\d)')[0]
print('total selected across the three sealed reads:', len(df))
print(df.groupby(['window','month']).agg(n=('actual_net_r','size'), net=('actual_net_r','sum'),
    resolved=('actual_net_r',lambda x: int(x.notna().sum()))).to_string())
df.to_pickle('frozen.pkl')
r=df[df.actual_net_r.notna()]
print('\nRESOLVED total:', len(r), ' pooled actual net R:', round(r.actual_net_r.sum(),4), ' mean', round(r.actual_net_r.mean(),5))
print('cost_r mean', round(r.cost_r.mean(),5), ' deductible mean', round(r.deductible_cost_r.mean(),5))
print('gross (net+deductible) mean', round((r.actual_net_r+r.deductible_cost_r).mean(),5))
print('precost (gross+spread since all MARKET) mean', round((r.actual_net_r+r.cost_r).mean(),5), ' total precost R', round((r.actual_net_r+r.cost_r).sum(),3))
print('TOTAL COST R paid:', round(r.cost_r.sum(),3))
