"""e1 step 2: per-month cost-gate forensics. Same instrument as l10x_06_recost,
extended with (a) spread PROVENANCE classification against the config table and
(b) the four months l10 never saw."""
import json, gzip, statistics as st, sys
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260725'.replace('20260725','20260801')
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
CFG=json.load(open('/tmp/e1x/e1_config_spread_table.json'))
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
JPYCOMM=0.00808905; USDCOMM=5.00048e-05
COMM={'EURUSD':USDCOMM,'GBPUSD':USDCOMM,'AUDUSD':USDCOMM,'NZDUSD':USDCOMM,'USDJPY':JPYCOMM,'GBPJPY':JPYCOMM,
 'EURJPY':JPYCOMM,'AUDJPY':JPYCOMM,'CHFJPY':JPYCOMM,'XAUUSD':0.0576,'XAGUSD':0.001}
SLIP={k:LIVE[k]['slip_px'] for k in LIVE}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
BTC_BPS=39.2778/88599.74*1e4
INDEX=('SPX500','NAS100','JP225','UK100','GER40','US30_cash')
def realbps(sym,key='spread_bps_median'):
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym))
    return tk.get(key) if tk else None
def commpx(sym,ep):
    if sym=='BTCUSD': return BTC_BPS*ep/1e4
    if sym=='ETHUSD': return 1.09905
    if sym in ('USDCHF','USDCAD'): return USDCOMM*ep
    if sym=='EURGBP': return USDCOMM*0.74
    return COMM.get(sym,0.0)
def q(v,p):
    v=sorted(v); return v[max(0,min(len(v)-1,int(round(p*(len(v)-1)))))]
def m(v): return round(st.mean(v),6) if v else None
def md(v): return round(st.median(v),6) if v else None

def run(month, path):
    rows=[]
    nall=0
    for l in gzip.open(path,'rt'):
        r=json.loads(l); nall+=1
        pool = (r['missed_opportunity_r_scoreability_status']=='diagnostic_opportunity_r_scoreable'
                and r['opportunity_net_proxy_r'] is not None)
        sym=r['symbol']; ep=r['entry_price']; sl=r['stop_loss']; spr=r['spread_r']; tc=r['expected_cost_r']
        if sym is None or ep in (None,0) or sl is None or spr is None or tc is None: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        rb=realbps(sym)
        if rb is None: continue
        real_spr=(rb*ep/1e4)/rd
        real_comm=commpx(sym,ep)/rd
        sp=SLIP.get(SLIPMAP.get(sym,''),0.0) or 0.0
        real_slip=max(sp,0.0)/rd
        cost_r = r['cost_r'] if r['cost_r'] is not None else tc
        gross = (r['opportunity_net_proxy_r']+cost_r) if r['opportunity_net_proxy_r'] is not None else None
        rows.append({'sym':sym,'pool':pool,'spr':spr,'tot':tc,'rd':rd,'ep':ep,'sprpx':spr*rd,
          'rspr':real_spr,'rtot':real_spr+real_comm+real_slip,'rcomm':real_comm,'rslip':real_slip,
          'gross':gross,'fam':r.get('origin_family'),'ses':r.get('route_session'),'hr':r.get('utc_hour_bucket')})
    out={'month':month,'ledger_rows':nall,'costable_rows':len(rows)}
    for popname,sel in (('POOL',lambda x:x['pool']),('FULL_LEDGER',lambda x:True)):
        R=[x for x in rows if sel(x)]
        n=len(R)
        if not n: continue
        pas_f=[x for x in R if x['spr']<=0.10+1e-12 and x['tot']<=0.15+1e-12]
        pas_r=[x for x in R if x['rspr']<=0.10+1e-12 and x['rtot']<=0.15+1e-12]
        idx=[x for x in R if x['sym'] in INDEX]
        blk={'n':n,
         'frozen_total_mean':m([x['tot'] for x in R]),'frozen_spread_mean':m([x['spr'] for x in R]),
         'real_total_mean':m([x['rtot'] for x in R]),'real_spread_mean':m([x['rspr'] for x in R]),
         'ratio_total':round(st.mean([x['tot'] for x in R])/st.mean([x['rtot'] for x in R]),4),
         'ratio_spread':round(st.mean([x['spr'] for x in R])/st.mean([x['rspr'] for x in R]),4),
         'gate_frozen_n_pass':len(pas_f),'gate_frozen_frac':round(len(pas_f)/n,5),
         'gate_real_n_pass':len(pas_r),'gate_real_frac':round(len(pas_r)/n,5),
         'gate_uplift_rows':len(pas_r)-len(pas_f),
         'gate_uplift_pct':round((len(pas_r)-len(pas_f))/max(1,len(pas_f))*100,2),
         'spread_limb_refuses_frozen':sum(1 for x in R if x['spr']>0.10),
         'total_limb_refuses_frozen':sum(1 for x in R if x['tot']>0.15),
         'spread_limb_share_of_frozen_refusals':round(sum(1 for x in R if x['spr']>0.10)/max(1,n-len(pas_f)),5),
         'INDEX_COMPLEX':{'n':len(idx),'share_of_pop':round(len(idx)/n,5),
            'frozen_cost_mean':m([x['tot'] for x in idx]),'real_cost_mean':m([x['rtot'] for x in idx]),
            'ratio':round(st.mean([x['tot'] for x in idx])/st.mean([x['rtot'] for x in idx]),3) if idx else None,
            'pass_frozen':sum(1 for x in idx if x['spr']<=0.10+1e-12 and x['tot']<=0.15+1e-12),
            'pass_real':sum(1 for x in idx if x['rspr']<=0.10+1e-12 and x['rtot']<=0.15+1e-12)}}
        g=[x['gross'] for x in R if x['gross'] is not None]
        if g:
            blk['gross_mean_all']=m(g)
            blk['gross_mean_pass_frozen']=m([x['gross'] for x in pas_f if x['gross'] is not None])
            blk['gross_mean_pass_real']=m([x['gross'] for x in pas_r if x['gross'] is not None])
            newly=[x for x in pas_r if not (x['spr']<=0.10+1e-12 and x['tot']<=0.15+1e-12) and x['gross'] is not None]
            blk['n_newly_admitted']=len(newly); blk['gross_mean_newly_admitted']=m([x['gross'] for x in newly])
            blk['net_real_pass_real']=m([x['gross']-x['rtot'] for x in pas_r if x['gross'] is not None])
            blk['net_real_pass_frozen']=m([x['gross']-x['rtot'] for x in pas_f if x['gross'] is not None])
        out[popname]=blk
    # per-symbol on POOL
    P=[x for x in rows if x['pool']] or rows
    per=defaultdict(list)
    for x in P: per[x['sym']].append(x)
    ps={}
    for s,v in sorted(per.items(),key=lambda kv:-len(kv[1])):
        pxs=[x['sprpx'] for x in v]; mn=st.mean(pxs)
        cv=round(st.pstdev(pxs)/mn,5) if mn else None
        ceil=CFG.get(s,{}).get('ceiling_px')
        prov='CEILING_AS_ESTIMATE' if (ceil and cv is not None and cv<1e-9 and abs(st.median(pxs)-ceil)<=1e-6*max(1,ceil)) \
             else ('CONSTANT_OTHER' if (cv is not None and cv<1e-9) else 'VARIES_TICK_LIKE')
        ps[s]={'n':len(v),'frozen_spread_px_median':round(st.median(pxs),8),'px_cv':cv,
          'config_ceiling_px':ceil,'provenance':prov,
          'frozen_spread_r_min':round(min(x['spr'] for x in v),6),'frozen_spread_r_median':md([x['spr'] for x in v]),
          'frozen_spread_bps':round(st.median([x['sprpx']/x['ep']*1e4 for x in v]),5),
          'real_spread_bps':realbps(s),
          'ratio_frozen_over_real_bps':round(st.median([x['sprpx']/x['ep']*1e4 for x in v])/realbps(s),4) if realbps(s) else None,
          'pass_frozen':sum(1 for x in v if x['spr']<=0.10+1e-12 and x['tot']<=0.15+1e-12),
          'pass_real':sum(1 for x in v if x['rspr']<=0.10+1e-12 and x['rtot']<=0.15+1e-12),
          'gross_mean':m([x['gross'] for x in v if x['gross'] is not None])}
    out['per_symbol_POOL']=ps
    return out

months=[('JAN','/tmp/e1x/e1_slice_JAN.jsonl.gz'),('FEB','/tmp/e1x/e1_slice_FEB.jsonl.gz'),
        ('MAR','/tmp/e1x/e1_slice_MAR.jsonl.gz'),('APR','/tmp/e1x/e1_slice_APR.jsonl.gz'),
        ('MAY','/tmp/e1x/e1_slice_MAY.jsonl.gz')]
res={}
for mth,p in months:
    res[mth]=run(mth,p); print('done',mth,res[mth]['ledger_rows'],res[mth]['costable_rows'],flush=True)
json.dump(res,open(f'{D}/E1_MONTHS_V1.json','w'),indent=1)
print('WROTE E1_MONTHS_V1.json')
