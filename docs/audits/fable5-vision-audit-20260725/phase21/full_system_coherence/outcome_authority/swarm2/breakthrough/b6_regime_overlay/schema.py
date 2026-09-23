import gzip, pickle, pandas as pd, numpy as np
rows=pickle.load(gzip.open('/private/tmp/w21-puzzle-cache/rows_feb.pkl.gz','rb'))
df=pd.DataFrame(rows)
print('n',len(df),'cols',len(df.columns))
for c in sorted(df.columns):
    s=df[c]
    try: nn=s.notna().sum()
    except Exception: nn=-1
    ex=s.dropna().iloc[0] if nn>0 else None
    print('%-46s %-10s nn=%6d  ex=%s'%(c,str(s.dtype),nn,str(ex)[:48]))
