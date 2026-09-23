import gzip, json, collections, statistics, math, os, sys

P='docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'
rows=[]
with gzip.open(P,'rt') as f:
    for line in f:
        rows.append(json.loads(line))
n=len(rows)
print('rows', n)
keys=list(rows[0].keys())
# verify all rows same key set
ks=set(map(lambda r: tuple(r.keys()), rows[:2000]))
print('distinct key-tuples in first 2000:', len(ks))
allk=set()
for r in rows: allk |= set(r.keys())
print('union keys', len(allk), 'first-row keys', len(keys), 'same', allk==set(keys))

out={}
for k in keys:
    vals=[r.get(k) for r in rows]
    nulls=sum(1 for v in vals if v is None)
    nn=[v for v in vals if v is not None]
    types=collections.Counter(type(v).__name__ for v in nn)
    card=len(set(map(repr,nn)))
    entry={'null_rate': round(nulls/n,6), 'nulls': nulls, 'dtypes': dict(types), 'cardinality': card}
    if nn and all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in nn):
        s=sorted(nn)
        entry['min']=s[0]; entry['max']=s[-1]
        entry['mean']=sum(s)/len(s)
        entry['median']=s[len(s)//2]
        entry['p05']=s[int(0.05*len(s))]; entry['p95']=s[int(0.95*len(s))]
        entry['constant']= (s[0]==s[-1])
    if card<=25:
        entry['values']=collections.Counter(map(lambda v: json.dumps(v) if not isinstance(v,str) else v, nn)).most_common(25)
    else:
        entry['top']=collections.Counter(map(lambda v: json.dumps(v) if not isinstance(v,str) else v, nn)).most_common(8)
    out[k]=entry

json.dump({'n':n,'fields':out}, open('/tmp/w0_pool_profile.json','w'), indent=1, default=str)
for k in keys:
    e=out[k]
    line=f"{k:52s} null={e['null_rate']:.4f} card={e['cardinality']:6d} dt={','.join(e['dtypes'].keys())}"
    if 'constant' in e and e['constant']: line+= f"  CONSTANT={e['min']}"
    elif 'min' in e: line+=f"  [{e['min']:.6g},{e['max']:.6g}] mean={e['mean']:.6g}"
    print(line)
