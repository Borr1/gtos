"""Portable decision anchor. Same rule as w0cap2_decision_anchor.py, any month.
mkt_r_prev_close = signed R of the CLOSE of the last fully-closed M1 bar strictly before
the decision minute.  born_past_stop iff <= -1.0.  Zero look-ahead (bars are open-stamped)."""
import json,gzip,os,sys,csv,bisect
BARROOT='/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars'
MONTHS=['202512','202601','202602','202603','202604','202605']
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
POOL=sys.argv[1]; OUT=sys.argv[2]; MONTHSET=sys.argv[3].split(',')
def load_sym(sym):
    ts=[];cl=[]
    for mo in MONTHSET:
        p=os.path.join(BARROOT,f'bridge_ftmo_m1_{mo}',f'{sym}_M1.csv')
        if not os.path.isfile(p): continue
        with open(p) as f:
            rd=csv.reader(f); next(rd)
            for r in rd: ts.append(r[0]); cl.append(float(r[4]))
    if not ts: return None
    z=sorted(zip(ts,cl))
    return {'t':[a for a,_ in z],'c':[b for _,b in z]}
pool=[]
for l in gzip.open(POOL,'rt'):
    r=json.loads(l); pool.append(r)
syms=sorted({r['symbol'] for r in pool})
cache={}; missing=[]
for s in syms:
    b=load_sym(s)
    if b is None: missing.append(s)
    else: cache[s]=b
out=[];nofit=0;nexact=0
for r in pool:
    sym=r['symbol']; b=cache.get(sym)
    if b is None: nofit+=1; continue
    ep=r.get('entry_price'); sl=r.get('stop_loss')
    if ep is None or sl is None: nofit+=1; continue
    d=abs(float(ep)-float(sl))
    if not d>0: nofit+=1; continue
    dt=r['decision_time_utc']
    i=bisect.bisect_right(b['t'],dt)-1
    if i<0: nofit+=1; continue
    exact=(b['t'][i]==dt); nexact+=1 if exact else 0
    j=i-1 if exact else i
    if j<0: j=0
    sgn=1.0 if r['side']=='LONG' else -1.0
    out.append({'candidate_id':r['candidate_id'],'decision_time_utc':dt,'symbol':sym,
      'mkt_r_prev_close':round(sgn*(b['c'][j]-float(ep))/d,6),'anchor_exact':exact,'anchor_bar_time':b['t'][i]})
with gzip.open(OUT,'wt') as f:
    for o in out: f.write(json.dumps(o)+'\n')
print(json.dumps({'pool':os.path.basename(POOL),'pool_rows':len(pool),'anchored':len(out),'no_fit':nofit,
  'missing_symbols':missing,'anchor_exact_share':round(nexact/max(1,len(out)),6),
  'past_stop':sum(1 for o in out if o['mkt_r_prev_close']<=-1.0)}))
