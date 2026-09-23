import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
OUT=f'{D}/L10X_POOL_RECOST_V1.json'
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
# commission in PRICE units, per pool symbol. MEASURED = read off real broker deals; MODELLED = class rule.
JPYCOMM=0.00808905   # measured ftmo:USDJPY and ftmo:GBPJPY and redacted_account:GBPJPY, identical to 4 s.f.
USDCOMM=5.00048e-05  # measured ftmo:EURUSD / ftmo:GBPUSD / redacted_account:GBPUSD
COMM={'EURUSD':(USDCOMM,'MEASURED'),'GBPUSD':(USDCOMM,'MEASURED'),'AUDUSD':(USDCOMM,'MODELLED_USD_QUOTED_FX'),
 'NZDUSD':(USDCOMM,'MODELLED_USD_QUOTED_FX'),
 'USDJPY':(JPYCOMM,'MEASURED'),'GBPJPY':(JPYCOMM,'MEASURED'),'EURJPY':(JPYCOMM,'MODELLED_JPY_QUOTED_FX'),
 'AUDJPY':(JPYCOMM,'MODELLED_JPY_QUOTED_FX'),'CHFJPY':(JPYCOMM,'MODELLED_JPY_QUOTED_FX'),
 'USDCHF':(None,'MODELLED_USD_BASE'),'USDCAD':(None,'MODELLED_USD_BASE'),'EURGBP':(None,'MODELLED_CROSS'),
 'XAUUSD':(0.0576,'MEASURED'),'XAGUSD':(0.001,'MODELLED_METAL_5000oz_at_5usd'),
 'UK100':(0.0,'MEASURED_ZERO'),'SPX500':(0.0,'MEASURED_ZERO'),'NAS100':(0.0,'MODELLED_INDEX_ZERO'),
 'US30_cash':(0.0,'MEASURED_ZERO'),'GER40':(0.0,'MEASURED_ZERO'),'JP225':(0.0,'MEASURED_ZERO'),
 'UKOIL_cash':(0.0,'MODELLED_CFD_ZERO'),'USOIL_cash':(0.0,'MODELLED_CFD_ZERO')}
CRYPTO_BPS={'BTCUSD':39.2778/88599.74*1e4,'ETHUSD':None}
SLIP={k:LIVE[k]['slip_px'] for k in LIVE}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
rows=[]
miss=defaultdict(int)
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l); sym=r['symbol']; ep=r['entry_price']; rd=r['risk_distance']
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym))
    if not tk or not tk.get('spread_bps_median'): miss[sym]+=1; continue
    sp_px=tk['spread_bps_median']*ep/1e4
    # commission
    if sym in CRYPTO_BPS and CRYPTO_BPS[sym]: cm=CRYPTO_BPS[sym]*ep/1e4; cb='MEASURED_NOTIONAL_FRACTION'
    elif sym=='ETHUSD': cm=1.09905/ (16.6103/0.0097999*1.0) if False else 1.09905; cb='MEASURED_ABS'
    elif sym in ('USDCHF','USDCAD'): cm=USDCOMM*ep; cb='MODELLED_USD_BASE'
    elif sym=='EURGBP': cm=USDCOMM*0.74; cb='MODELLED_CROSS'
    else:
        v=COMM.get(sym); cm,cb=(v[0],v[1]) if v and v[0] is not None else (0.0,'UNMODELLED_ZERO')
    sl_px=SLIP.get(SLIPMAP.get(sym,''),None)
    if sl_px is None: sl_px=0.0; sb='UNMODELLED_ZERO'
    else: sb='MEASURED'
    sl_px=max(sl_px,0.0)
    rows.append({'sym':sym,'rd':rd,'ep':ep,'gross':r['gross_r'],'froz_spr':r['spread_r'],'froz_tot':r['expected_cost_r'],
      'real_spr':sp_px/rd,'real_comm':cm/rd,'real_slip':sl_px/rd,'cb':cb,'sb':sb,'fam':r.get('origin_family')})
for x in rows: x['real_tot']=x['real_spr']+x['real_comm']+x['real_slip']
def m(v): return round(st.mean(v),6) if v else None
def med(v): return round(st.median(v),6) if v else None
n=len(rows)
res={'n_rows_costed':n,'n_missing':dict(miss),
 'method':'real spread = FTMO tick-archive median spread in bps of mid (2026-06-18..07-24, full population per symbol) applied to each row entry price; real commission and slippage = live broker deals converted to price units (comm_r*sl_distance) and re-denominated by the ROW risk_distance. Swap charged 0 (2 h horizon).',
 'POOL_COST_R':{'frozen_total_mean':m([x['froz_tot'] for x in rows]),'frozen_spread_mean':m([x['froz_spr'] for x in rows]),
   'real_total_mean':m([x['real_tot'] for x in rows]),'real_spread_mean':m([x['real_spr'] for x in rows]),
   'real_comm_mean':m([x['real_comm'] for x in rows]),'real_slip_mean':m([x['real_slip'] for x in rows]),
   'frozen_total_median':med([x['froz_tot'] for x in rows]),'real_total_median':med([x['real_tot'] for x in rows]),
   'ratio_frozen_over_real_total':round(st.mean([x['froz_tot'] for x in rows])/st.mean([x['real_tot'] for x in rows]),3),
   'ratio_frozen_over_real_spread':round(st.mean([x['froz_spr'] for x in rows])/st.mean([x['real_spr'] for x in rows]),3)},
 'GROSS_MEAN':m([x['gross'] for x in rows])}
# gate counterfactual
def gate(x,spr,tot): return (spr<=0.10+1e-12) and (tot<=0.15+1e-12)
for lbl,fs,ft in [('FROZEN',lambda x:x['froz_spr'],lambda x:x['froz_tot']),('REAL',lambda x:x['real_spr'],lambda x:x['real_tot'])]:
    pas=[x for x in rows if gate(x,fs(x),ft(x))]
    res[f'GATE_{lbl}']={'n_pass':len(pas),'frac_pass':round(len(pas)/n,5),
      'gross_mean_of_passed':m([x['gross'] for x in pas]),
      'net_at_real_cost':m([x['gross']-x['real_tot'] for x in pas]),
      'net_at_frozen_cost':m([x['gross']-x['froz_tot'] for x in pas]),
      'spread_limb_refuses':sum(1 for x in rows if fs(x)>0.10),'total_limb_refuses':sum(1 for x in rows if ft(x)>0.15)}
res['ALL_ROWS_NET']={'net_at_frozen':m([x['gross']-x['froz_tot'] for x in rows]),'net_at_real':m([x['gross']-x['real_tot'] for x in rows])}
per=defaultdict(list)
for x in rows: per[x['sym']].append(x)
res['per_symbol']={k:{'n':len(v),'froz_spr_med':med([x['froz_spr'] for x in v]),'real_spr_med':med([x['real_spr'] for x in v]),
  'ratio':round(med([x['froz_spr'] for x in v])/med([x['real_spr'] for x in v]),3) if med([x['real_spr'] for x in v]) else None,
  'real_tot_med':med([x['real_tot'] for x in v]),'gross_mean':m([x['gross'] for x in v]),
  'n_pass_real':sum(1 for x in v if gate(x,x['real_spr'],x['real_tot'])),'n_pass_frozen':sum(1 for x in v if gate(x,x['froz_spr'],x['froz_tot'])),
  'comm_basis':v[0]['cb'],'slip_basis':v[0]['sb']} for k,v in sorted(per.items(),key=lambda kv:-len(kv[1]))}
json.dump(res,open(OUT,'w'),indent=1)
print(json.dumps({k:v for k,v in res.items() if k!='per_symbol'},indent=1)[:1800])
print(f"{'sym':<12}{'n':>6}{'frozSprR':>10}{'realSprR':>10}{'ratio':>8}{'realTotR':>10}{'grossR':>9}{'passF':>7}{'passR':>7}")
for k,v in res['per_symbol'].items():
    print(f"{k:<12}{v['n']:>6}{v['froz_spr_med']:>10.4f}{v['real_spr_med']:>10.4f}{str(v['ratio']):>8}{v['real_tot_med']:>10.4f}{v['gross_mean']:>9.4f}{v['n_pass_frozen']:>7}{v['n_pass_real']:>7}")
