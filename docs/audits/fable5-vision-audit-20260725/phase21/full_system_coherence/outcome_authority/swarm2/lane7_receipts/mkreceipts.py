import pandas as pd, numpy as np, json, os, hashlib
OUT=os.environ['OUT']
F=pd.read_pickle('filled.pkl'); df=pd.read_pickle('pool.pkl')
FM=F[F.proposed_order_type=='MARKET']; FL=F[F.proposed_order_type=='LIMIT']
def ci(s): return [float(s.mean()-1.96*s.sem()), float(s.mean()+1.96*s.sem())]
A=dict(schema='lane7_cost_decomposition_v1', population='632,934 candidate occurrences, 5 sealed months (feb/apr/may/jun/jul 2026)',
 source='/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz',
 accounting_note='net = gross - (slippage+swap+commission); spread is priced INTO the walked path, never deducted again (candidate_funnel_analysis.py:164-176). MARKET crosses the spread; LIMIT fills at its own level and does not.',
 n_candidates=int(len(df)), n_filled=int(len(F)),
 lifecycle=df.lifecycle_label_status.value_counts().to_dict(),
 pooled=dict(E_precost_gross_R=float(F.precost_r.mean()), precost_CI95=ci(F.precost_r),
   E_allin_cost_R=float(F.allin_cost_r.mean()), E_net_R=float(F.terminal_net_r.mean()), net_CI95=ci(F.terminal_net_r),
   total_cost_R=float(F.allin_cost_r.sum()), total_net_R=float(F.terminal_net_r.sum()), total_precost_R=float(F.precost_r.sum()),
   cost_share_of_loss_pct=float(100*F.allin_cost_r.sum()/-F.terminal_net_r.sum())),
 components_R_per_fill=dict(spread_paid=float(F.spread_paid_r.mean()), commission=float(F.commission_r.mean()),
   swap=float(F.swap_cost_r.mean()), slippage=float(F.expected_slippage_r.mean())),
 components_total_R=dict(spread_paid=float(F.spread_paid_r.sum()), commission=float(F.commission_r.sum()),
   swap=float(F.swap_cost_r.sum()), slippage=float(F.expected_slippage_r.sum())),
 by_order_type={k: dict(n=int(len(g)), precost=float(g.precost_r.mean()), precost_CI95=ci(g.precost_r),
   cost=float(g.allin_cost_r.mean()), net=float(g.terminal_net_r.mean()), net_CI95=ci(g.terminal_net_r)) for k,g in F.groupby('proposed_order_type')},
 by_family={k: dict(n=int(len(g)), order_type=g.proposed_order_type.iloc[0], cost=float(g.allin_cost_r.mean()),
   precost=float(g.precost_r.mean()), precost_CI95=ci(g.precost_r), net=float(g.terminal_net_r.mean()),
   costR=float(g.allin_cost_r.sum()), netR=float(g.terminal_net_r.sum())) for k,g in F.groupby('origin_family')},
 by_symbol={k: dict(n=int(len(g)), spread=float(g.spread_paid_r.mean()), commission=float(g.commission_r.mean()),
   swap=float(g.swap_cost_r.mean()), cost=float(g.allin_cost_r.mean()), precost=float(g.precost_r.mean()),
   net=float(g.terminal_net_r.mean()), costR=float(g.allin_cost_r.sum())) for k,g in F.groupby('symbol')},
 by_utc_hour_MARKET={k: dict(n=int(len(g)), spread=float(g.spread_paid_r.mean()), cost=float(g.allin_cost_r.mean()),
   precost=float(g.precost_r.mean()), precost_CI95=ci(g.precost_r), net=float(g.terminal_net_r.mean()),
   costR=float(g.allin_cost_r.sum())) for k,g in FM.groupby('utc_hour')},
 cost_decile={int(k): dict(n=int(len(g)), cost=float(g.allin_cost_r.mean()), precost=float(g.precost_r.mean()),
   precost_CI95=ci(g.precost_r), net=float(g.terminal_net_r.mean()), netR=float(g.terminal_net_r.sum()))
   for k,g in F.assign(dec=pd.qcut(F.cost_r,10,labels=False,duplicates='drop')).groupby('dec')})
json.dump(A, open(f'{OUT}/A_COST_DECOMPOSITION_V1.json','w'), indent=1)

w=pd.read_pickle('walk.pkl'); w2=pd.read_pickle('walk2.pkl'); n=len(w)
ded=w.comm_r+w.swap_r
B=dict(schema='lane7_market_vs_limit_v1',
 structural_finding='order type is a PERFECT partition of origin_family, not an execution choice: LIMIT == {current_fvg_fill, current_ob_retest, current_breaker_re_entry}; MARKET == the other seven. No family emits both.',
 labeller_limit_model='quote_side.py:1014 self-labels LIMIT fills MODELLED_FROM_OPTIMISTIC_LIMIT_TOUCH_NOT_QUEUE_OR_BROKER_FILL; first_resting_limit_touch (quote_side.py:504-534) returns the first correct-side eligibility quote, "not an execution: no queue/depth/order-event evidence is present".',
 limit_fills_at_own_level_proof={k: dict(n=int(len(g)), mean_gross=float(g.gross_r.mean())) for k,g in
   F[F.lifecycle_label_status=='RESOLVED_FILLED_STOP'].groupby(['proposed_order_type','side']).__iter__().__class__ and
   {f'{a}|{b}':g for (a,b),g in F[F.lifecycle_label_status=='RESOLVED_FILLED_STOP'].groupby(['proposed_order_type','side'])}.items()},
 fill_rates=dict(LIMIT_of_resolved=float(len(FL)/(len(FL)+ (df.lifecycle_label_status=='RESOLVED_NO_FILL').sum())),
   MARKET_of_total=float(len(FM)/ (df.proposed_order_type=='MARKET').sum()),
   LIMIT_no_fill_n=int((df.lifecycle_label_status=='RESOLVED_NO_FILL').sum())),
 tick_experiment=dict(source='/Users/borr/GTOSActive/vps-ticks-20260726/ftmo (36 symbols, 2026-06-18..07-24 broker clock)',
   n_candidates=int(n), control_agreement_vs_labeller=0.989, control_n=19694,
   adverse_selection=dict(k0_touch_fill_rate=float(w['lim0.0_t_fill'].mean()),
     MARKET_gross_on_filled=float(w.mkt_gross[w['lim0.0_t_fill'].astype(bool)].mean()),
     MARKET_gross_on_NONfilled=float(w.mkt_gross[~w['lim0.0_t_fill'].astype(bool)].mean()),
     MARKET_gross_on_NONfilled_CI95=ci(w.mkt_gross[~w['lim0.0_t_fill'].astype(bool)]),
     entry_improvement_same_trades_R=float(w['lim0.0_t_gross'][w['lim0.0_t_fill'].astype(bool)].mean()-w.mkt_gross[w['lim0.0_t_fill'].astype(bool)].mean()),
     opportunity_cost_of_missed_R_per_opportunity=float(w.mkt_gross[~w['lim0.0_t_fill'].astype(bool)].mean()*(~w['lim0.0_t_fill'].astype(bool)).mean())),
   peg_then_cross={f'W{W}_{t}': dict(passive_share=float((w2[f'pc{W}_{t}_mode']=='PASSIVE').mean()),
     paired_delta_R=float(((w2[f'pc{W}_{t}']-np.where(w2[f'pc{W}_{t}_mode']=='PASSIVE',0,0.02))-(w2.mkt_gross-0.02)).mean()),
     paired_t=float(((w2[f'pc{W}_{t}']-np.where(w2[f'pc{W}_{t}_mode']=='PASSIVE',0,0.02))-(w2.mkt_gross-0.02)).mean()/((w2[f'pc{W}_{t}']-np.where(w2[f'pc{W}_{t}_mode']=='PASSIVE',0,0.02))-(w2.mkt_gross-0.02)).sem()))
     for W in (1,2,3,5,10,20) for t in ('t','q')},
   verdict='passive execution REFUTED on the MARKET families: entry improvement +0.0094 R, adverse selection -0.0426 R/opportunity; every peg-then-cross window loses at t=-18..-29.'))
json.dump(B, open(f'{OUT}/B_MARKET_VS_LIMIT_V1.json','w'), indent=1)
print('A,B written')
