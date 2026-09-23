"""Measure the M15 -> H4 ATR14 ratio on the archive, so AR-3's timeframe claim is a measurement."""
import json,gzip,sys,statistics,importlib.util,collections
from pathlib import Path
REPO=Path('.').resolve(); sys.path.insert(0,str(REPO))
AUD=REPO/"docs/audits/fable5-vision-audit-20260725"
def _load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
AD=_load(AUD/"phase7/receipts/ad_exit_sweep.py","atr_ad")
from src.components.ultimate_book.primitives import atr14
series,index,_=AD.load_bars()
raw=json.load(gzip.open(AUD/"phase6/receipts/AA_ESTATE_TRADES.json.gz","rt"))
syms=sorted({r['symbol'] for r in raw['trades']['asia_pdl_fade']})
print(f"asia_pdl_fade symbols: {len(syms)}  M15={AD.TF_M15} H4={AD.TF_H4}")
ratios=[]
for s in syms:
    k15,k4=(s,AD.TF_M15),(s,AD.TF_H4)
    if k15 not in series or k4 not in series: 
        print(f"  {s:12s} missing {'M15' if k15 not in series else 'H4'}"); continue
    b15,_=series[k15]; b4,_=series[k4]
    a15=[atr14(b15,i) for i in range(200,len(b15),max(1,len(b15)//400))]
    a4 =[atr14(b4,i)  for i in range(200,len(b4), max(1,len(b4)//400))]
    a15=[x for x in a15 if x and x>0]; a4=[x for x in a4 if x and x>0]
    if not a15 or not a4: continue
    r=statistics.median(a4)/statistics.median(a15)
    ratios.append((s,r,statistics.median(a15),statistics.median(a4)))
    print(f"  {s:12s} median ATR14  M15 {statistics.median(a15):.6g}  H4 {statistics.median(a4):.6g}  ratio {r:.3f}")
rs=[r for _,r,_,_ in ratios]
print()
print(f"n symbols {len(rs)}  median ratio {statistics.median(rs):.3f}  mean {statistics.fmean(rs):.3f}  "
      f"min {min(rs):.3f}  max {max(rs):.3f}")
print(f"sqrt(240/15) = sqrt(16) = 4.000  <- the random-walk approximation")
json.dump({"n_symbols":len(rs),"median_ratio":statistics.median(rs),"mean_ratio":statistics.fmean(rs),
           "min":min(rs),"max":max(rs),"sqrt_time_approx":4.0,
           "per_symbol":{s:{"ratio":r,"median_atr14_m15":m15,"median_atr14_h4":m4} for s,r,m15,m4 in ratios}},
          open('/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave11-conditioning-sizing-20260730/e02391db-fc9f-445c-8371-6708b63399fa/scratchpad/atr_ratio.json','w'),indent=1)
