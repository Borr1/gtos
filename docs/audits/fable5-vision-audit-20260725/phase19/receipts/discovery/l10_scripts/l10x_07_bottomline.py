import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
OUT=f'{D}/L10X_BOTTOMLINE_V1.json'
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
JPYC=0.00808905; USDC=5.00048e-05
COMM={'EURUSD':USDC,'GBPUSD':USDC,'AUDUSD':USDC,'NZDUSD':USDC,'USDJPY':JPYC,'GBPJPY':JPYC,'EURJPY':JPYC,
 'AUDJPY':JPYC,'CHFJPY':JPYC,'XAUUSD':0.0576,'XAGUSD':0.001,'UK100':0.0,'SPX500':0.0,'NAS100':0.0,
 'US30_cash':0.0,'GER40':0.0,'JP225':0.0,'UKOIL_cash':0.0,'USOIL_cash':0.0,'EURGBP':USDC*0.74}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
anch={}
for l in gzip.open(f'{D}/w0cap2_DECISION_ANCHOR_V1.jsonl.gz','rt'):
    a=json.loads(l); anch[(a['candidate_id'],a['decision_time_utc'])]=a.get('mkt_r_prev_close')
rows=[]; nomatch=0
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l); sym=r['symbol']; ep=r['entry_price']; rd=r['risk_distance']
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym)); 
    m=anch.get((r['candidate_id'],r['decision_time_utc']))
    if m is None: nomatch+=1; bs='UNANCHORED'
    else: bs=bo(m)
    cm=COMM.get(sym, USDC*ep if sym in ('USDCHF','USDCAD') else (39.2778/88599.74*ep if sym=='BTCUSD' else (1.09905 if sym=='ETHUSD' else 0.0)))
    slp=max(LIVE.get(SLIPMAP.get(sym,''),{}).get('slip_px',0.0) or 0.0,0.0)
    rs=tk['spread_bps_median']*ep/1e4/rd
    rows.append({'sym':sym,'bs':bs,'gross':r['gross_r'],'froz_spr':r['spread_r'],'froz_tot':r['expected_cost_r'],
      'rspr':rs,'rcm':cm/rd,'rsl':slp/rd,'fam':r.get('origin_family')})
for x in rows: x['rtot']=x['rspr']+x['rcm']+x['rsl']
def m_(v): return round(st.mean(v),6) if v else None
N=len(rows)
tk=[x for x in rows if x['bs']!='born_past_stop']
res={'n':N,'n_unanchored':nomatch,'n_takeable_ex_past_stop':len(tk),
 'method':'gross_r is fill-blind path value (cost-free). born_past_stop from W0-capture rule mkt_r_prev_close<=-1.0. real cost = FTMO tick median spread + measured broker commission + measured slippage, re-denominated by each row risk_distance; swap 0 at the 2 h horizon.'}
def book(rr,lbl):
    if not rr: return None
    return {'n':len(rr),'gross':m_([x['gross'] for x in rr]),'frozen_cost':m_([x['froz_tot'] for x in rr]),
            'real_cost':m_([x['rtot'] for x in rr]),'net_frozen':m_([x['gross']-x['froz_tot'] for x in rr]),
            'net_real':m_([x['gross']-x['rtot'] for x in rr])}
res['A_all_rows']=book(rows,'all')
res['B_takeable_only']=book(tk,'tk')
g=lambda x,s,t:(s<=0.10+1e-12 and t<=0.15+1e-12)
res['C_takeable_at_frozen_gate']=book([x for x in tk if g(x,x['froz_spr'],x['froz_tot'])],'')
res['D_takeable_at_real_gate']=book([x for x in tk if g(x,x['rspr'],x['rtot'])],'')
res['E_takeable_real_gate_and_cheapest_decile']=None
srt=sorted([x for x in tk if g(x,x['rspr'],x['rtot'])],key=lambda x:x['rtot'])
res['E_takeable_real_gate_cheapest_half']=book(srt[:len(srt)//2],'')
# index complex exclusion
IDX=['SPX500','NAS100','JP225','UK100','GER40','US30_cash']
ix=[x for x in rows if x['sym'] in IDX]
res['INDEX_COMPLEX']={'symbols':IDX,'n':len(ix),'frac_of_pool':round(len(ix)/N,4),
  'n_pass_frozen':sum(1 for x in ix if g(x,x['froz_spr'],x['froz_tot'])),
  'n_pass_real':sum(1 for x in ix if g(x,x['rspr'],x['rtot'])),
  'gross_mean':m_([x['gross'] for x in ix]),
  'gross_mean_takeable':m_([x['gross'] for x in ix if x['bs']!='born_past_stop']),
  'real_cost_mean':m_([x['rtot'] for x in ix]),'frozen_cost_mean':m_([x['froz_tot'] for x in ix]),
  'net_real_takeable':m_([x['gross']-x['rtot'] for x in ix if x['bs']!='born_past_stop'])}
per=defaultdict(list)
for x in tk: per[x['sym']].append(x)
res['per_symbol_takeable']={k:{'n':len(v),'gross':m_([x['gross'] for x in v]),'real_cost':m_([x['rtot'] for x in v]),
   'net_real':m_([x['gross']-x['rtot'] for x in v]),'n_pass_real_gate':sum(1 for x in v if g(x,x['rspr'],x['rtot']))}
   for k,v in sorted(per.items(),key=lambda kv:-len(kv[1]))}
pf=defaultdict(list)
for x in tk: pf[x['fam']].append(x)
res['per_family_takeable']={str(k):{'n':len(v),'gross':m_([x['gross'] for x in v]),'real_cost':m_([x['rtot'] for x in v]),
   'net_real':m_([x['gross']-x['rtot'] for x in v])} for k,v in sorted(pf.items(),key=lambda kv:-len(kv[1]))}
json.dump(res,open(OUT,'w'),indent=1)
for k in ['A_all_rows','B_takeable_only','C_takeable_at_frozen_gate','D_takeable_at_real_gate','E_takeable_real_gate_cheapest_half']:
    print(k, json.dumps(res[k]))
print('INDEX', json.dumps(res['INDEX_COMPLEX']))
print(f"{'sym':<12}{'n':>6}{'gross':>10}{'realCost':>10}{'netReal':>10}{'passR':>7}")
for k,v in res['per_symbol_takeable'].items():
    print(f"{k:<12}{v['n']:>6}{v['gross']:>10.4f}{v['real_cost']:>10.4f}{v['net_real']:>10.4f}{v['n_pass_real_gate']:>7}")
