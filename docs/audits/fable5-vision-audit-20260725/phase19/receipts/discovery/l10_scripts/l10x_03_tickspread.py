import gzip, json, math, os, glob, sys
from collections import defaultdict
OUT='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L10X_TICK_SPREAD_V1.json'
ROOT='/Users/borr/GTOSActive/vps-ticks-20260726'
BIN=200.0  # log10 bins: 0.5% resolution
def q(hist, total, p):
    if total==0: return None
    tgt=p*total; c=0
    for k in sorted(hist):
        c+=hist[k]
        if c>=tgt: return round(10**(k/BIN),6)
    return None
res={}
files=sorted(glob.glob(f'{ROOT}/ftmo/*.csv.gz'))+sorted(glob.glob(f'{ROOT}/redacted_account/*.csv.gz'))
print(f'{len(files)} files', flush=True)
for fi,f in enumerate(files):
    base=os.path.basename(f)
    brk='ftmo' if '/ftmo/' in f else 'redacted_account'
    sym=base.split('_ticks_')[0].split('_',1)[1]
    hist=defaultdict(int); hh=defaultdict(lambda: defaultdict(int))
    tot=0; mids=[]; zero=0; neg=0; bad=0; midsum=0.0
    with gzip.open(f,'rt') as fh:
        fh.readline()
        for line in fh:
            p=line.split(',')
            try:
                t=int(p[0]); b=float(p[1]); a=float(p[2])
            except Exception:
                bad+=1; continue
            if b<=0 or a<=0: bad+=1; continue
            sp=a-b
            if sp<0: neg+=1; continue
            mid=(a+b)*0.5
            if sp==0: zero+=1
            bps=sp/mid*1e4
            tot+=1; midsum+=mid
            if bps>0:
                k=int(round(math.log10(bps)*BIN)); hist[k]+=1
                hh[(t//3600)%24][k]+=1
    nz=sum(hist.values())
    ent={'broker':brk,'symbol':sym,'n_ticks':tot,'n_zero_spread':zero,'n_negative':neg,'n_bad':bad,
         'mean_mid':round(midsum/tot,6) if tot else None,
         'spread_bps_p10':q(hist,nz,.10),'spread_bps_median':q(hist,nz,.50),
         'spread_bps_p25':q(hist,nz,.25),'spread_bps_p75':q(hist,nz,.75),
         'spread_bps_p90':q(hist,nz,.90),'spread_bps_p99':q(hist,nz,.99)}
    ent['spread_bps_median_by_broker_hour']={str(h):q(hh[h],sum(hh[h].values()),.50) for h in sorted(hh)}
    ent['n_by_broker_hour']={str(h):sum(hh[h].values()) for h in sorted(hh)}
    res[f'{brk}:{sym}']=ent
    print(f'[{fi+1}/{len(files)}] {brk}:{sym} n={tot} med={ent["spread_bps_median"]}', flush=True)
    json.dump(res,open(OUT,'w'),indent=1)
print('DONE', flush=True)
