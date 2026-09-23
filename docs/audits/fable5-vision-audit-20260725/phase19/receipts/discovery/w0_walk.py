import gzip, json, collections
POOL='docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'
SIDE='docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz'
pool={}
for l in gzip.open(POOL,'rt'):
    r=json.loads(l); pool[(r['candidate_id'],r['decision_time_utc'])]=r
res=collections.Counter(); tt=[]; ts=[]; mfe=[]; open_at_wall=0; n=0
band_first=collections.Counter()
for l in gzip.open(SIDE,'rt'):
    row=json.loads(l); k=(row['candidate_id'],row['decision_time_utc'])
    p=pool.get(k)
    if p is None: continue
    obs=row['ordered_path_observations']
    if not obs: continue
    n+=1
    e=p['entry_price']; s=p['stop_loss']; d=abs(e-s); side=p['side']
    ti=si=None; rf=0.0
    for i,b in enumerate(obs):
        hi=b['high']; lo=b['low']
        if side=='LONG': f=(hi-e)/d; a=(e-lo)/d
        else: f=(e-lo)/d; a=(hi-e)/d
        if f>rf: rf=f
        if si is None and a>=1.0-1e-12: si=i
        if ti is None and f>=2.0-1e-12: ti=i
        if si is not None and ti is not None: break
    mfe.append(rf)
    if si is not None and (ti is None or si<=ti):
        res['stop_first']+=1; ts.append(si+1)
        if ti is not None and ti==si: res['same_bar_ambiguity']+=1
    elif ti is not None:
        res['target_first']+=1; tt.append(ti+1)
    else:
        res['neither_by_120min']+=1; open_at_wall+=1
    if rf>=2.0: band_first['mfe>=2R']+=1
    elif rf>=1.0: band_first['1R<=mfe<2R']+=1
    elif rf>=0.5: band_first['0.5<=mfe<1R']+=1
    else: band_first['mfe<0.5R']+=1
print('walked',n)
print('outcome by 2R/1R first-touch within 120 min:',{k:(v,round(v/n,4)) for k,v in res.items()})
tt.sort(); ts.sort()
print('minutes-to-TARGET  n=%d p05=%d med=%d p95=%d max=%d'%(len(tt),tt[int(.05*len(tt))],tt[len(tt)//2],tt[int(.95*len(tt))],tt[-1]))
print('minutes-to-STOP    n=%d p05=%d med=%d p95=%d max=%d'%(len(ts),ts[int(.05*len(ts))],ts[len(ts)//2],ts[int(.95*len(ts))],ts[-1]))
mfe.sort()
print('MFE (R): p25 %.3f med %.3f p75 %.3f p90 %.3f p99 %.3f max %.3f'%(mfe[int(.25*n)],mfe[n//2],mfe[int(.75*n)],mfe[int(.90*n)],mfe[int(.99*n)],mfe[-1]))
print('MFE bands:',{k:(v,round(v/n,4)) for k,v in band_first.most_common()})
# how many stops occur in the LAST 10 minutes / target after 100 min
print('targets hit in final 20 min of the 120-min window:',sum(1 for x in tt if x>100),'=%.1f%% of targets'%(100*sum(1 for x in tt if x>100)/len(tt)))
json.dump({'walked':n,'outcomes':dict(res),'minutes_to_target_median':tt[len(tt)//2],'minutes_to_stop_median':ts[len(ts)//2],
 'mfe_median':mfe[n//2],'mfe_p90':mfe[int(.9*n)],'mfe_bands':dict(band_first)}, open('/tmp/w0_walk.json','w'), indent=1)
