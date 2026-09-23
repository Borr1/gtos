import sys, os, numpy as np, pandas as pd, json
path=sys.argv[1]; out=sys.argv[2]
base=os.path.basename(path)
broker='FTMO' if base.startswith('FTMO') else 'redacted_account'
sym=base.split('_ticks_')[0].replace('FTMO_','').replace('redacted_account_','')
OFF=3*3600
acc={}
n_tot=0
for ch in pd.read_csv(path, usecols=['time','bid','ask'], dtype={'time':'int64','bid':'float64','ask':'float64'}, chunksize=4_000_000):
    n_tot+=len(ch)
    b=ch['bid'].values; a=ch['ask'].values; t=ch['time'].values
    ok=np.isfinite(b)&np.isfinite(a)&(b>0)&(a>0)&(a>=b)
    b=b[ok]; a=a[ok]; t=t[ok]
    mk=(t-OFF)//60
    o=np.argsort(mk,kind='stable'); mk=mk[o]; b=b[o]; a=a[o]
    uk,idx=np.unique(mk,return_index=True)
    end=np.append(idx[1:],len(mk))
    cnt=(end-idx).astype('float64')
    bh=np.maximum.reduceat(b,idx); bl=np.minimum.reduceat(b,idx)
    ah=np.maximum.reduceat(a,idx); al=np.minimum.reduceat(a,idx)
    bo=b[idx]; bc=b[end-1]; ao=a[idx]; ac=a[end-1]
    ssum=np.add.reduceat(a-b,idx)
    for i,k in enumerate(uk):
        r=acc.get(k)
        v=[cnt[i],bo[i],bh[i],bl[i],bc[i],ao[i],ah[i],al[i],ac[i],ssum[i]]
        if r is None: acc[k]=v
        else:
            r[0]+=v[0]; r[2]=max(r[2],v[2]); r[3]=min(r[3],v[3]); r[4]=v[4]
            r[6]=max(r[6],v[6]); r[7]=min(r[7],v[7]); r[8]=v[8]; r[9]+=v[9]
ks=np.array(sorted(acc.keys()),dtype='int64'); M=np.array([acc[k] for k in ks],dtype='float64')
np.savez_compressed(out, minute_utc=ks, n=M[:,0], bo=M[:,1],bh=M[:,2],bl=M[:,3],bc=M[:,4],
                    ao=M[:,5],ah=M[:,6],al=M[:,7],ac=M[:,8], sp_sum=M[:,9], symbol=sym, broker=broker, n_ticks=n_tot)
print(json.dumps({'file':base,'symbol':sym,'broker':broker,'ticks':int(n_tot),'minutes':len(ks)}))
