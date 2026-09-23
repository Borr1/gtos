import json, gzip, statistics as st, datetime as dt
from collections import defaultdict, Counter
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
OUT=f'{D}/L10X_HOURS_MINSTOP_V1.json'
OFF=3  # broker hour = true UTC hour + 3 (MEASURED l10x_01)
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
# tick availability per pool symbol by TRUE UTC hour
avail={}
for ps,ts in TMAP.items():
    e=TICK.get('ftmo:'+ts)
    if not e: continue
    h=e['n_by_broker_hour']; tot=sum(h.values())
    ut={}
    for bh,n in h.items(): ut[(int(bh)-OFF)%24]=ut.get((int(bh)-OFF)%24,0)+n
    avail[ps]={'total':tot,'by_true_utc_hour':{str(k):v for k,v in sorted(ut.items())},
               'share':{str(k):round(v/tot,6) for k,v in sorted(ut.items())}}
# pool decision hours + risk distance per symbol
ph=defaultdict(Counter); rd=defaultdict(list); ep=defaultdict(list)
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l); s=r['symbol']
    ph[s][dt.datetime.fromisoformat(r['decision_time_utc']).hour]+=1
    rd[s].append(r['risk_distance']); ep[s].append(r['entry_price'])
res={'method':'tick availability = share of all FTMO ticks for that instrument falling in each TRUE UTC hour (broker hour - 3, measured). Pool hours = decision_time_utc hour, already true UTC (CJ re-clock).',
     'thin_hour_threshold':'an hour holding <0.5% of the instrument daily tick mass is called THIN'}
rows={}; tot_thin=0; tot=0
for s,c in ph.items():
    a=avail.get(s)
    if not a: continue
    n=sum(c.values()); tot+=n
    thin=sum(v for h,v in c.items() if a['share'].get(str(h),0.0)<0.005)
    dead=sum(v for h,v in c.items() if a['share'].get(str(h),0.0)==0.0)
    tot_thin+=thin
    med_rd=st.median(rd[s]); med_ep=st.median(ep[s])
    tk=TICK['ftmo:'+TMAP[s]]
    spr_px=tk['spread_bps_median']*med_ep/1e4
    rows[s]={'n_pool':n,'pool_rows_in_thin_hours':thin,'frac_thin':round(thin/n,4),
      'pool_rows_in_zero_tick_hours':dead,
      'median_risk_distance':round(med_rd,8),'median_risk_pct_of_price':round(med_rd/med_ep*100,5),
      'real_spread_price':round(spr_px,8),
      'min_stop_for_spread_under_0p10R':round(spr_px/0.10,8),
      'min_stop_pct_for_spread_under_0p10R':round(spr_px/0.10/med_ep*100,5),
      'stop_widen_factor_needed':round((spr_px/0.10)/med_rd,3)}
res['per_symbol']=dict(sorted(rows.items(), key=lambda kv:-kv[1]['stop_widen_factor_needed']))
res['pool_summary']={'n':tot,'rows_in_thin_hours':tot_thin,'frac':round(tot_thin/tot,4),
   'median_widen_factor':round(st.median([v['stop_widen_factor_needed'] for v in rows.values()]),3),
   'n_symbols_already_wide_enough':sum(1 for v in rows.values() if v['stop_widen_factor_needed']<=1.0)}
res['availability_by_symbol']=avail
json.dump(res,open(OUT,'w'),indent=1)
print(json.dumps(res['pool_summary'],indent=1))
print(f"{'sym':<12}{'nPool':>6}{'thin%':>8}{'zeroHr':>7}{'stop%':>9}{'sprPx':>11}{'minStop%':>10}{'widenX':>8}")
for k,v in res['per_symbol'].items():
    print(f"{k:<12}{v['n_pool']:>6}{100*v['frac_thin']:>8.2f}{v['pool_rows_in_zero_tick_hours']:>7}{v['median_risk_pct_of_price']:>9.4f}{v['real_spread_price']:>11.6g}{v['min_stop_pct_for_spread_under_0p10R']:>10.4f}{v['stop_widen_factor_needed']:>8.2f}")
