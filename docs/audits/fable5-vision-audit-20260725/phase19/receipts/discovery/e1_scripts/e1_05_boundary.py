"""e1 step 5: (a) portable cross-month control (drop current_breaker_re_entry, which is
98.61% of the January past-stop artifact), (b) the TWO-SIDED distortion cohorts,
(c) family / session / hour boundary."""
import json, gzip, statistics as st
from collections import defaultdict
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
CEIL_COHORT=('SPX500','NAS100','JP225','UK100','GER40','US30_cash','ETHUSD','EURJPY','CHFJPY')
FLOOR_COHORT=('USOIL_cash','UKOIL_cash','BTCUSD','XAUUSD','XAGUSD','USDJPY')
def rb(s):
    t=TICK.get('ftmo:'+TMAP.get(s,s)); return t.get('spread_bps_median') if t else None
def commpx(s,ep):
    if s=='BTCUSD': return BTC_BPS*ep/1e4
    if s=='ETHUSD': return 1.09905
    if s in ('USDCHF','USDCAD'): return USDCOMM*ep
    if s=='EURGBP': return USDCOMM*0.74
    return COMM.get(s,0.0)
def m(v): return round(st.mean(v),6) if v else None
def load(mo):
    R=[]
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
        if r['opportunity_net_proxy_r'] is None: continue
        ep,sl,spr,tc=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r']
        if ep in (None,0) or sl is None or spr is None or tc is None: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        b=rb(r['symbol'])
        if b is None: continue
        cost=r['cost_r'] if r['cost_r'] is not None else tc
        rspr=(b*ep/1e4)/rd
        rtot=rspr+commpx(r['symbol'],ep)/rd+max(SLIP.get(SLIPMAP.get(r['symbol'],''),0.0) or 0.0,0.0)/rd
        R.append({'rdp':rd/abs(ep)*100.0,'g':r['opportunity_net_proxy_r']+cost,'spr':spr,'tot':tc,
          'rspr':rspr,'rtot':rtot,'pf':(spr<=0.10+1e-12 and tc<=0.15+1e-12),
          'pr':(rspr<=0.10+1e-12 and rtot<=0.15+1e-12),
          'sym':r['symbol'],'fam':r['origin_family'],'ses':r['route_session'],'hr':r['utc_hour_bucket']})
    return R
def gateedge(S):
    S=sorted(S,key=lambda x:x['rdp']); n=len(S)
    if n<100: return None
    p=[x['g'] for x in S if x['pf']]
    if not p: return None
    w=[]
    for i in range(10):
        a,b=int(i*n/10),int((i+1)*n/10); s=S[a:b]
        a1=[x['g'] for x in s if x['pf']]; b1=[x['g'] for x in s if not x['pf']]
        w.append((len(a1),(st.mean(a1)-st.mean(b1)) if a1 and b1 else None))
    tot=sum(k for k,d in w if d is not None)
    d1=[x['g'] for x in S[:int(n/10)]]; d10=[x['g'] for x in S[int(9*n/10):]]
    return {'n':n,'n_pass':len(p),'gross_all':m([x['g'] for x in S]),'gross_pass':m(p),
      'raw_edge':round(st.mean(p)-st.mean([x['g'] for x in S]),6),
      'stopwidth_matched_edge':round(sum(k*d for k,d in w if d is not None)/max(1,tot),6),
      'd1_gross':m(d1),'d10_gross':m(d10),'d10_minus_d1':round(st.mean(d10)-st.mean(d1),6)}
res={}
for mo in ('JAN','FEB','MAR','APR','MAY'):
    R=load(mo)
    NB=[x for x in R if x['fam']!='current_breaker_re_entry']
    o={'n_pool':len(R),'n_ex_breaker':len(NB),
       'ALL':gateedge(R),'EX_BREAKER':gateedge(NB)}
    # two-sided cohorts
    for lab,cohort in (('CEILING_OVERCHARGED',CEIL_COHORT),('FLOOR_UNDERCHARGED',FLOOR_COHORT)):
        C=[x for x in R if x['sym'] in cohort]
        o[lab]={'n':len(C),'share':round(len(C)/len(R),5),
          'frozen_cost_mean':m([x['tot'] for x in C]),'real_cost_mean':m([x['rtot'] for x in C]),
          'ratio':round(st.mean([x['tot'] for x in C])/st.mean([x['rtot'] for x in C]),3) if C else None,
          'pass_frozen':sum(1 for x in C if x['pf']),'pass_real':sum(1 for x in C if x['pr']),
          'gross_mean':m([x['g'] for x in C]),
          'gross_mean_pass_frozen':m([x['g'] for x in C if x['pf']]),
          'gross_mean_pass_real':m([x['g'] for x in C if x['pr']])}
    # family boundary: overcharge ratio and gate deletion
    fam=defaultdict(list)
    for x in R: fam[x['fam']].append(x)
    o['per_family']={k:{'n':len(v),'ratio_frozen_over_real':round(st.mean([x['tot'] for x in v])/st.mean([x['rtot'] for x in v]),3),
        'pass_frozen':sum(1 for x in v if x['pf']),'pass_real':sum(1 for x in v if x['pr']),
        'gross':m([x['g'] for x in v]),'gross_pf':m([x['g'] for x in v if x['pf']]),
        'gross_pr':m([x['g'] for x in v if x['pr']]),
        'median_rdp':round(st.median([x['rdp'] for x in v]),5)} for k,v in sorted(fam.items(),key=lambda kv:-len(kv[1]))}
    ses=defaultdict(list)
    for x in R: ses[x['ses']].append(x)
    o['per_session']={k:{'n':len(v),'ratio':round(st.mean([x['tot'] for x in v])/st.mean([x['rtot'] for x in v]),3),
        'pass_frozen':sum(1 for x in v if x['pf']),'pass_real':sum(1 for x in v if x['pr']),'gross':m([x['g'] for x in v])}
        for k,v in sorted(ses.items(),key=lambda kv:-len(kv[1]))}
    res[mo]=o
json.dump(res,open(f'{D}/E1_BOUNDARY_V1.json','w'),indent=1)
print(f"{'mo':<5}{'nAll':>7}{'rawEdge':>9}{'mEdge':>8}{'d10-d1':>9} | {'nExBrk':>7}{'rawEdge':>9}{'mEdge':>8}{'d10-d1':>9}")
for mo,v in res.items():
    a,b=v['ALL'],v['EX_BREAKER']
    print(f"{mo:<5}{a['n']:>7}{a['raw_edge']:>9.4f}{a['stopwidth_matched_edge']:>8.4f}{a['d10_minus_d1']:>9.4f} | {b['n']:>7}{b['raw_edge']:>9.4f}{b['stopwidth_matched_edge']:>8.4f}{b['d10_minus_d1']:>9.4f}")
print()
print(f"{'mo':<5}{'CEIL n':>8}{'ratio':>7}{'pF':>6}{'pR':>6}{'gross':>9}{'gPF':>9}{'gPR':>9} | {'FLOOR n':>8}{'ratio':>7}{'pF':>6}{'pR':>6}{'gross':>9}")
for mo,v in res.items():
    c=v['CEILING_OVERCHARGED']; f=v['FLOOR_UNDERCHARGED']
    print(f"{mo:<5}{c['n']:>8}{c['ratio']:>7.2f}{c['pass_frozen']:>6}{c['pass_real']:>6}{c['gross_mean']:>9.4f}{(c['gross_mean_pass_frozen'] or 0):>9.4f}{(c['gross_mean_pass_real'] or 0):>9.4f} | {f['n']:>8}{f['ratio']:>7.2f}{f['pass_frozen']:>6}{f['pass_real']:>6}{f['gross_mean']:>9.4f}")
