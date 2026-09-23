import sys, json, gzip, glob, os
sys.path.insert(0,'/tmp/f1')
from paths import ARM
KEEP=None
out={}
for w,p in sorted(ARM.items()):
    f=glob.glob(p+'/*TRADE_LEDGER*')[0]
    op=gzip.open if f.endswith('.gz') else open
    rows=[]
    with op(f,'rt') as fh:
        for line in fh:
            r=json.loads(line)
            rows.append(r)
    out[w]=rows
    if w=='2026-01':
        print('JAN rows',len(rows))
        ks=sorted(rows[0].keys())
        print('nkeys',len(ks))
        print(ks)
    else:
        print(w,'rows',len(rows))
json.dump({k:len(v) for k,v in out.items()},open('/tmp/f1/trade_ledger_counts.json','w'))
import pickle
pickle.dump(out,open('/tmp/f1/trade_ledgers.pkl','wb'))
