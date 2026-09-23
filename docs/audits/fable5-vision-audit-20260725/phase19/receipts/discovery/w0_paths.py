import gzip, json, collections, datetime as dt
P='docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz'
POOL='docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'

pool_keys=set(); pool_cid=set(); pool_n=0
with gzip.open(POOL,'rt') as f:
    for line in f:
        r=json.loads(line); pool_n+=1
        pool_keys.add((r['candidate_id'], r['decision_time_utc']))
        pool_cid.add(r['candidate_id'])
print('pool rows',pool_n,'distinct (cid,dt)',len(pool_keys),'distinct cid',len(pool_cid))

n=0; nbars=[]; keys=set(); dupes=0
tick_src=0; tf=collections.Counter(); horiz=collections.Counter(); sides=collections.Counter()
schema=collections.Counter(); arm=collections.Counter(); syms=collections.Counter()
bar_keys=collections.Counter(); zero=0
first_lag=collections.Counter()
srcpath_tf=collections.Counter()
with gzip.open(P,'rt') as f:
    for line in f:
        r=json.loads(line); n+=1
        k=(r['candidate_id'], r['decision_time_utc'])
        if k in keys: dupes+=1
        keys.add(k)
        obs=r['ordered_path_observations']
        nbars.append(len(obs))
        if len(obs)==0: zero+=1
        else:
            bar_keys[tuple(sorted(obs[0].keys()))]+=1
            d0=dt.datetime.fromisoformat(r['decision_time_utc']); t0=dt.datetime.fromisoformat(obs[0]['time_utc'])
            first_lag[int((t0-d0).total_seconds())]+=1
        if r.get('ordered_tick_source'): tick_src+=1
        tf[r.get('source_timeframe')]+=1
        schema[r['schema']]+=1; arm[r['arm_id']]+=1; sides[r['side']]+=1; syms[r['symbol']]+=1
        dd=dt.datetime.fromisoformat(r['decision_time_utc']); hh=dt.datetime.fromisoformat(r['horizon_end_utc'])
        horiz[(hh-dd).total_seconds()/60.0]+=1
        srcpath_tf[r['source_path'].split('/')[1]]+=1

nb=sorted(nbars)
print('sidecar rows',n,'distinct keys',len(keys),'dupes',dupes)
print('bars: min',nb[0],'p05',nb[int(.05*len(nb))],'median',nb[len(nb)//2],'p95',nb[int(.95*len(nb))],'max',nb[-1],'mean',sum(nb)/len(nb),'zero-bar rows',zero)
print('bars histogram (top12)',collections.Counter(nb).most_common(12))
print('tick_source present',tick_src, tick_src/n)
print('source_timeframe',dict(tf))
print('horizon minutes',horiz.most_common(10))
print('side',dict(sides)); print('arm',dict(arm)); print('schema',dict(schema))
print('bar dict keys',bar_keys.most_common(3))
print('first-bar lag seconds',first_lag.most_common(6))
print('source_path bucket',srcpath_tf.most_common(6))
print('COVERAGE: pool rows with a path (by cid,dt):', len(pool_keys & keys), '=', len(pool_keys&keys)/pool_n)
print('sidecar keys not in pool:', len(keys - pool_keys))
print('symbols in sidecar',len(syms))
json.dump({'sidecar_rows':n,'distinct_keys':len(keys),'bars_median':nb[len(nb)//2],'bars_min':nb[0],'bars_max':nb[-1],
 'bars_mean':sum(nb)/len(nb),'zero_bar':zero,'tick_source_rows':tick_src,'coverage_pool_rows':len(pool_keys&keys),
 'pool_rows':pool_n,'pool_distinct_keys':len(pool_keys),'horizon_minutes':dict((str(k),v) for k,v in horiz.items()),
 'bars_hist':dict((str(k),v) for k,v in collections.Counter(nb).most_common(30))}, open('/tmp/w0_paths_profile.json','w'), indent=1)
