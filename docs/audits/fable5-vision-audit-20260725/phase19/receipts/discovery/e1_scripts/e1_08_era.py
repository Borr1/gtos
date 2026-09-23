"""e1 step 8: ROBUSTNESS. l10's 'real' spread is the FTMO tick median measured 2026-06-18..07-24
and applied to Jan-May 2026. src/costs/spread_model.py carries measured ERA ratios. Ask it whether
Jan-May 2026 spreads differ from the July snapshot, and re-price the headline at the era-true level
and at the model's high band."""
import sys, json, datetime as dt, statistics as st
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from src.costs import spread_model as sm
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
MAP={'SPX500':'US500.cash','NAS100':'US100.cash','JP225':'JP225.cash','UK100':'UK100.cash','GER40':'GER40.cash',
     'US30_cash':'US30.cash','USOIL_cash':'USOIL.cash','UKOIL_cash':'UKOIL.cash'}
SY=['SPX500','NAS100','JP225','UK100','GER40','US30_cash','ETHUSD','EURJPY','CHFJPY','XAUUSD','XAGUSD','BTCUSD',
    'USOIL_cash','UKOIL_cash','EURUSD','GBPUSD','USDJPY','AUDUSD','NZDUSD','USDCAD','USDCHF','EURGBP','GBPJPY','AUDJPY']
MONTHS=[('JAN',dt.datetime(2026,1,15,12,tzinfo=dt.timezone.utc)),('FEB',dt.datetime(2026,2,13,12,tzinfo=dt.timezone.utc)),
        ('MAR',dt.datetime(2026,3,13,12,tzinfo=dt.timezone.utc)),('APR',dt.datetime(2026,4,15,12,tzinfo=dt.timezone.utc)),
        ('MAY',dt.datetime(2026,5,15,12,tzinfo=dt.timezone.utc)),('JUL_REF',dt.datetime(2026,7,1,12,tzinfo=dt.timezone.utc))]
out={'note':'spread_price(account=FTMO, band=mid, composition default). price = quoted spread in price units.'}
tab={}
for s in SY:
    b=MAP.get(s,s); row={}
    for lab,t in MONTHS:
        try:
            e=sm.spread_price(b,'FTMO',t,band='mid'); e_hi=sm.spread_price(b,'FTMO',t,band='high')
            row[lab]={'mid':round(e.spread_price,10),'high':round(e_hi.spread_price,10),
                      'coverage':str(getattr(e,'coverage',None)),'era':getattr(e,'era',None),'era_ratio':getattr(e,'era_ratio',None),'era_class':getattr(e,'era_class',None),
                      'decidable':getattr(e,'decidable',None)}
        except Exception as ex: row[lab]={'error':f'{type(ex).__name__}:{str(ex)[:60]}'}
    tab[s]=row
out['per_symbol']=tab
rat={}
for s,row in tab.items():
    ref=row.get('JUL_REF',{}).get('mid')
    if not ref: continue
    rat[s]={mo:(round(row[mo]['mid']/ref,4) if row.get(mo,{}).get('mid') else None) for mo,_ in MONTHS[:5]}
    rat[s]['high_over_mid_JAN']=round(row['JAN']['high']/row['JAN']['mid'],4) if row.get('JAN',{}).get('mid') else None
out['era_ratio_month_over_july']=rat
json.dump(out,open(f'{D}/E1_ERA_SPREAD_V1.json','w'),indent=1)
print(f"{'sym':<12}{'JUL_mid':>12}{'JAN_mid':>12}{'JAN/JUL':>9}{'FEB':>8}{'MAR':>8}{'APR':>8}{'MAY':>8}{'hi/mid':>8}{'cov':>12}")
for s in SY:
    r=tab[s]; j=r.get('JUL_REF',{}); a=r.get('JAN',{})
    if 'error' in j or 'error' in a: print(f"{s:<12}  {j.get('error') or a.get('error')}"); continue
    q=rat[s]
    print(f"{s:<12}{j['mid']:>12.6g}{a['mid']:>12.6g}{(q['JAN'] or 0):>9.3f}{(q['FEB'] or 0):>8.3f}{(q['MAR'] or 0):>8.3f}{(q['APR'] or 0):>8.3f}{(q['MAY'] or 0):>8.3f}{(q['high_over_mid_JAN'] or 0):>8.3f}{str(a.get('coverage'))[:11]:>12}")
