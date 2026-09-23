"""e1 step 4: THE CONTROL. Does the stop-width -> gross gradient survive removing the
born_past_stop artifact (W0-capture: 12.72% of the Jan pool, mechanically -0.9948 R)?
January only - the anchor exists only for January."""
import json, gzip, statistics as st, math
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260725'.replace('20260725','20260801')
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
anc={}
for l in gzip.open(f'{D}/w0cap2_DECISION_ANCHOR_V1.jsonl.gz','rt'):
    r=json.loads(l); anc[(r['candidate_id'],r['decision_time_utc'])]=bo(r['mkt_r_prev_close'])  # CLEAN no-look-ahead anchor (reproduces w0-capture 14911/7949/1265/3516)
R=[]
for l in gzip.open('/tmp/e1x/e1_slice_JAN.jsonl.gz','rt'):
    r=json.loads(l)
    if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
    if r['opportunity_net_proxy_r'] is None: continue
    ep,sl,spr,tc=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r']
    if ep in (None,0) or sl is None or spr is None or tc is None: continue
    rd=abs(ep-sl)
    if rd<=0: continue
    cost=r['cost_r'] if r['cost_r'] is not None else tc
    R.append({'rdp':rd/abs(ep)*100.0,'g':r['opportunity_net_proxy_r']+cost,'spr':spr,'tot':tc,
      'pf':(spr<=0.10+1e-12 and tc<=0.15+1e-12),'sym':r['symbol'],'fam':r['origin_family'],
      'bs':anc.get((r['candidate_id'],r['decision_time_utc']))})
def m(v): return round(st.mean(v),6) if v else None
def deciles(S,label):
    S=sorted(S,key=lambda x:x['rdp']); n=len(S); out=[]
    for i in range(10):
        a,b=int(i*n/10),int((i+1)*n/10); s=S[a:b]
        if not s: continue
        out.append({'d':i+1,'n':len(s),'rdp_lo':round(s[0]['rdp'],5),'rdp_hi':round(s[-1]['rdp'],5),
          'gross':m([x['g'] for x in s]),'frac_pass_frozen':round(sum(1 for x in s if x['pf'])/len(s),4),
          'past_stop_pct':round(100*sum(1 for x in s if x['bs']=='born_past_stop')/len(s),2)})
    return {'label':label,'n':n,'gross':m([x['g'] for x in S]),
      'd1_gross':out[0]['gross'],'d10_gross':out[-1]['gross'],
      'spread_d10_minus_d1':round(out[-1]['gross']-out[0]['gross'],6),'deciles':out}
res={'n_all':len(R),'anchor_missing':sum(1 for x in R if x['bs'] is None)}
res['ALL']=deciles(R,'ALL')
CL=[x for x in R if x['bs'] and x['bs']!='born_past_stop']
res['EX_PAST_STOP']=deciles(CL,'EX_PAST_STOP')
res['BORN_RESTING_ONLY']=deciles([x for x in R if x['bs']=='born_resting'],'BORN_RESTING_ONLY')
res['BORN_AT_LIMIT_ONLY']=deciles([x for x in R if x['bs']=='born_at_limit'],'BORN_AT_LIMIT_ONLY')
# gate edge, raw and stop-width matched, on the clean set
for lab,S in (('ALL',R),('EX_PAST_STOP',CL)):
    S2=sorted(S,key=lambda x:x['rdp']); n=len(S2)
    p=[x['g'] for x in S2 if x['pf']]; 
    within=[]
    for i in range(10):
        a,b=int(i*n/10),int((i+1)*n/10); s=S2[a:b]
        a1=[x['g'] for x in s if x['pf']]; b1=[x['g'] for x in s if not x['pf']]
        within.append((len(a1),(st.mean(a1)-st.mean(b1)) if a1 and b1 else None))
    tot=sum(k for k,d in within if d is not None)
    res[f'GATE_EDGE_{lab}']={'n':n,'n_pass':len(p),'gross_all':m([x['g'] for x in S2]),'gross_pass':m(p),
      'raw_edge':round(st.mean(p)-st.mean([x['g'] for x in S2]),6),
      'stopwidth_matched_edge':round(sum(k*d for k,d in within if d is not None)/max(1,tot),6)}
# past-stop rate by stop-width decile is in deciles already
json.dump(res,open(f'{D}/E1_CONTROL_PASTSTOP_V2.json','w'),indent=1)
for k in ('ALL','EX_PAST_STOP','BORN_RESTING_ONLY','BORN_AT_LIMIT_ONLY'):
    v=res[k]; print(f"{k:<20} n={v['n']:>6} gross={v['gross']:>9.4f} d1={v['d1_gross']:>9.4f} d10={v['d10_gross']:>9.4f} d10-d1={v['spread_d10_minus_d1']:>9.4f}")
print()
print('EX_PAST_STOP deciles:'); print(f"{'d':>3}{'n':>7}{'rdp_lo':>9}{'rdp_hi':>9}{'gross':>9}{'passFroz':>10}{'pastStop%':>11}")
for d in res['EX_PAST_STOP']['deciles']:
    print(f"{d['d']:>3}{d['n']:>7}{d['rdp_lo']:>9.4f}{d['rdp_hi']:>9.4f}{d['gross']:>9.4f}{d['frac_pass_frozen']:>10.4f}{d['past_stop_pct']:>11.2f}")
print()
print('ALL deciles past-stop share:', [d['past_stop_pct'] for d in res['ALL']['deciles']])
print('GATE_EDGE:', {k:res[k] for k in res if k.startswith('GATE_EDGE')})
