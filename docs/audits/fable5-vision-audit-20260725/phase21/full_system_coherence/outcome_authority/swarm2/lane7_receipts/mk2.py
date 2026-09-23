import pandas as pd, numpy as np, json, os
OUT=os.environ['OUT']
F=pd.read_pickle('filled.pkl'); w=pd.read_pickle('walk.pkl'); FMt=pd.read_pickle('mkt_true.pkl')
def ci(s): return [float(s.mean()-1.96*s.sem()), float(s.mean()+1.96*s.sem())]
# C: envelope ladder
sw=F.groupby(['symbol','side']).swap_cost_r.mean().unstack()
adv={s:('LONG' if sw.loc[s,'LONG']<=sw.loc[s,'SHORT'] else 'SHORT') for s in sw.index}
F['fav']=[adv[s]==sd for s,sd in zip(F.symbol,F.side)]
BADH={'16','17','18','19','20','21'}; months=['feb','apr','may','jun','jul']
lad=[('L0_all',lambda d,th:np.ones(len(d),bool)),
     ('L1_drop_hours_16_21',lambda d,th: ~d.utc_hour.isin(BADH).values),
     ('L2_plus_favourable_carry_side',lambda d,th: (~d.utc_hour.isin(BADH).values)&d.fav.values),
     ('L3_plus_cost_le_OOSmedian',lambda d,th: (~d.utc_hour.isin(BADH).values)&d.fav.values&(d.cost_r.values<=th[0])),
     ('L4_plus_cost_le_OOSp25',lambda d,th: (~d.utc_hour.isin(BADH).values)&d.fav.values&(d.cost_r.values<=th[1])),
     ('L5_plus_cost_le_OOSp10',lambda d,th: (~d.utc_hour.isin(BADH).values)&d.fav.values&(d.cost_r.values<=th[2]))]
C={'schema':'lane7_cost_envelope_v1','design':'leave-one-month-out: thresholds fit on the other four months, applied to the held-out month. cost_r is a GENERATION-TIME field, known before the outcome.','ladder':{}}
for name,fn in lad:
    tn=0;tnet=0.;tc=0.;tp=0.;per={}
    for m in months:
        tr=F[F._m!=m]; te=F[F._m==m]; th=(tr.cost_r.quantile(.5),tr.cost_r.quantile(.25),tr.cost_r.quantile(.10))
        s=te[fn(te,th)]; per[m]=float(s.terminal_net_r.mean()); tn+=len(s); tnet+=s.terminal_net_r.sum(); tc+=s.allin_cost_r.sum(); tp+=s.precost_r.sum()
    C['ladder'][name]=dict(n=int(tn), breadth_pct=float(100*tn/len(F)), cost=float(tc/tn), precost=float(tp/tn), net=float(tnet/tn), totR=float(tnet), per_month_net=per)
C['headline']='cost 0.21332 -> 0.03636 (-83%); net -0.23209 -> -0.03421 (+0.198 R/fill, 85% of the loss removed); pre-cost gross -0.01878 -> +0.00215 (does NOT degrade). NO month turns positive at any rung.'
json.dump(C, open(f'{OUT}/C_COST_ENVELOPE_V1.json','w'), indent=1)
# D: slippage
S=w[w.mkt_state=='STOP'].copy(); S['gap_open_r']=S.stop_gap_open_px/S.risk; S['gap_r']=S.stop_gap_px/S.risk
v=S.gap_open_r.dropna()
D=dict(schema='lane7_slippage_v1', model_charge='expected_slippage_r is the constant 0.02 on all 632,934 rows (no dispersion)',
 n_stops=int(len(S)), stop_share_of_fills=float((w.mkt_state=='STOP').mean()),
 gap_at_trigger_open=dict(mean_R=float(v.mean()), median=float(v.median()), p90=float(v.quantile(.9)), p99=float(v.quantile(.99)),
   frac_gapped=float((v>0.001).mean()), CI95=ci(v)),
 max_penetration_inside_trigger_minute=dict(mean_R=float(S.gap_r.mean()), median=float(S.gap_r.median()), p99=float(S.gap_r.quantile(.99))),
 verdict=f'measured stop slippage {v.mean():.5f} R/stop x stop share {(w.mkt_state=="STOP").mean():.4f} = {v.mean()*(w.mkt_state=="STOP").mean():.5f} R/fill expected, vs 0.02 charged on ALL fills. The model is under-charging by >= {v.mean()*(w.mkt_state=="STOP").mean()-0.02:.5f} R/fill on the stop leg alone, and over-charging the target leg (a limit exit pays no slippage).',
 by_symbol={k: dict(n=int(len(g)), mean_gap_R=float(g.gap_open_r.mean()), p95=float(g.gap_open_r.quantile(.95)), frac_gapped=float((g.gap_open_r>0.001).mean())) for k,g in S.groupby('symbol')},
 by_hour={int(k): dict(n=int(len(g)), mean_gap_R=float(g.gap_open_r.mean())) for k,g in S.groupby('hour')})
json.dump(D, open(f'{OUT}/D_SLIPPAGE_AND_STOP_FILLS_V1.json','w'), indent=1)
# E: broker
bs=pd.read_json('broker_spread.json')
E=dict(schema='lane7_broker_arbitrage_v1', source='true tick spreads, both hosts, identical 2026-06-18..07-24 window, 300,538,915 ticks',
 note='the export directory holds 61 files / 300,538,915 rows, not the 51 files / 263,894,769 rows CLAUDE.md records',
 per_symbol=bs.to_dict(orient='records'),
 cheaper_on_FTMO=int((bs.fn_over_ftmo>1.02).sum()), cheaper_on_redacted_account=int((bs.fn_over_ftmo<0.98).sum()), within_2pct=int(((bs.fn_over_ftmo>=.98)&(bs.fn_over_ftmo<=1.02)).sum()),
 headline='25 shared instruments, ZERO within 2%. FTMO cheaper on 16, redacted_account on 9. Largest: BTCUSD FN is 19.72x FTMO in relative spread; JP225 1.95x; USDCHF 1.99x; USDJPY 1.72x. redacted_account is cheaper on CHFJPY 0.69x, EURJPY 0.88x, GBPJPY 0.88x, ETHUSD 0.89x, NZDUSD 0.89x.')
json.dump(E, open(f'{OUT}/E_BROKER_INSTRUMENT_ARBITRAGE_V1.json','w'), indent=1)
# F: swap
p=F.pivot_table(index='symbol',columns='side',values='swap_cost_r',aggfunc='mean')
c=F.pivot_table(index='symbol',columns='side',values='swap_cost_r',aggfunc='size')
Fv=dict(schema='lane7_swap_v1', total_swap_R=float(F.swap_cost_r.sum()), mean_R_per_fill=float(F.swap_cost_r.mean()),
 frac_fills_zero_swap=float((F.swap_cost_r==0).mean()),
 per_symbol_side={s: dict(LONG=float(p.loc[s,'LONG']), SHORT=float(p.loc[s,'SHORT']), n_LONG=int(c.loc[s,'LONG']), n_SHORT=int(c.loc[s,'SHORT']),
   favourable_side=adv[s], asymmetry=float(p.loc[s,'LONG']-p.loc[s,'SHORT'])) for s in p.index},
 favourable_side_restriction=dict(
   adverse=dict(n=int((~F.fav).sum()), swap=float(F.swap_cost_r[~F.fav].mean()), cost=float(F.allin_cost_r[~F.fav].mean()),
     precost=float(F.precost_r[~F.fav].mean()), precost_CI95=ci(F.precost_r[~F.fav]), net=float(F.terminal_net_r[~F.fav].mean())),
   favourable=dict(n=int(F.fav.sum()), swap=float(F.swap_cost_r[F.fav].mean()), cost=float(F.allin_cost_r[F.fav].mean()),
     precost=float(F.precost_r[F.fav].mean()), precost_CI95=ci(F.precost_r[F.fav]), net=float(F.terminal_net_r[F.fav].mean())),
   saving_R_per_fill=float(F.allin_cost_r[~F.fav].mean()-F.allin_cost_r[F.fav].mean()),
   gross_cost_of_the_restriction=float(F.precost_r[F.fav].mean()-F.precost_r[~F.fav].mean())))
json.dump(Fv, open(f'{OUT}/F_SWAP_CROSS_SECTION_V1.json','w'), indent=1)
print('C,D,E,F written')
