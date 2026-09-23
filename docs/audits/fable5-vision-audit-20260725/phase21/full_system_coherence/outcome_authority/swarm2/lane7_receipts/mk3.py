import pandas as pd, numpy as np, json, os
OUT=os.environ['OUT']
r=pd.read_pickle('frozen3.pkl'); w=pd.read_pickle('walk.pkl'); FMt=pd.read_pickle('mkt_true.pkl')
months=['2026-02','2026-04','2026-05','2026-06','2026-07']
w['ratio']=w.true_spread_px/w.model_spread_px.replace(0,np.nan)
byh=w.groupby(['symbol','hour']).agg(n=('ratio','size'),model=('model_spread_px','mean'),true=('true_spread_px','mean'),ratio=('ratio','median')).reset_index()
G=dict(schema='lane7_spread_model_truth_and_restatement_v1',
 method='per (symbol, UTC hour) median of true_tick_spread / modelled_spread, measured at the first strictly-post-decision minute on 21,684 MARKET candidates that fall inside the FTMO tick archive (2026-06-18..07-24). Control: this harness reproduces the sealed labeller on 98.9% of 19,694 resolved candidates.',
 defect='the spread model is hour-FLAT for the cash indices while the tape is not. UK100 modelled 0.86-1.12 at every hour; true 0.67 (h11) to 5.99 (h20), a 9x range. Ratio 4.4-4.7x in hours 00-05, 0.78-0.91 in hours 07-14. GER40 the same shape (2.6-2.7x vs 0.93-0.97). SPX500/NAS100/US30/JP225 are correct at every hour (0.93-1.06).',
 per_symbol_hour=byh.to_dict(orient='records'),
 pool_restatement=dict(n=int(len(FMt)), modelled_cost=float(FMt.allin_cost_r.mean()), tape_true_cost=float(FMt.cost_true.mean()),
   modelled_net=float(FMt.terminal_net_r.mean()), tape_true_net=float(FMt.net_true.mean()),
   extra_spread_R_per_fill=float(FMt.extra.mean()), extra_spread_total_R=float(FMt.extra.sum()),
   undercharge_pct_of_total_cost=float(100*FMt.extra.mean()/FMt.allin_cost_r.mean())),
 frozen_rule_restatement=dict(n=int(len(r)), sealed_net_R=float(r.actual_net_r.sum()), tape_true_net_R=float(r.net_true.sum()),
   extra_R=float(r.extra.sum()), sealed_cost_R=float(r.cost_r.sum()), tape_true_cost_R=float((r.cost_r+r.extra).sum()),
   gross_R=float((r.actual_net_r+r.cost_r).sum()),
   per_month={m: dict(n=int((r.month==m).sum()), sealed=float(r.actual_net_r[r.month==m].sum()), tape_true=float(r.net_true[r.month==m].sum()), extra=float(r.extra[r.month==m].sum())) for m in months},
   direct_evidence_window=dict(window='2026-06 + 2026-07 (ticks overlap)', n=int(r.month.isin(months[3:]).sum()),
     sealed=float(r.actual_net_r[r.month.isin(months[3:])].sum()), tape_true=float(r.net_true[r.month.isin(months[3:])].sum())),
   concentration='74 of 282 trades (26.2%) are UK100, the symbol whose modelled spread is 2.48x too small; it carries 7.081 of the 7.04 R correction'),
 adversarial_check='the first pass used the MEAN tick spread and produced a -14.9 R restatement. UK100 spread is bimodal (median 0.85, mean 2.11) so the mean overstated it. Redone hour-conditionally against the model as it is actually applied, the correction is +7.04 R, not +15.8 R. The finding survives the check; its size does not.',
 headline='the sealed five-month frozen-rule record restates from +0.954 R to -6.090 R once spreads are priced from the tape rather than the model. February PASS survives (+14.168 -> +14.062); the correction lands almost entirely on June (+3.964 -> +1.176) and July (-14.566 -> -18.727).')
json.dump(G, open(f'{OUT}/G_SPREAD_MODEL_TRUTH_AND_RESTATEMENT_V1.json','w'), indent=1)
# H: program
F=pd.read_pickle('filled.pkl')
H=dict(schema='lane7_program_v1',
 frozen_rule_monthly=dict(trades_per_month=float(len(r)/5), gross_R_per_month=float((r.actual_net_r+r.cost_r).sum()/5),
   cost_R_per_month_modelled=float(r.cost_r.sum()/5), cost_R_per_month_tape_true=float((r.cost_r+r.extra).sum()/5),
   net_R_per_month_sealed=float(r.actual_net_r.sum()/5), net_R_per_month_tape_true=float(r.net_true.sum()/5),
   cost_share_of_gross_pct=float(100*r.cost_r.sum()/(r.actual_net_r+r.cost_r).sum())),
 recoverable=dict(halving_rule_cost_R_per_month_modelled=float(r.cost_r.sum()/10),
   halving_rule_cost_R_per_month_tape_true=float((r.cost_r+r.extra).sum()/10),
   pool_ladder_saving_R_per_fill=0.19788, pool_ladder_saving_pct_of_loss=85.3),
 steps=[
  dict(rank=1, change='fix the cash-index spread model to be hour-conditional (UK100, GER40)', saves_R_per_month='0.0 (it is an ACCOUNTING repair, not a saving) — but it moves the sealed 5-month record from +0.954 R to -6.090 R and June/July from +3.964/-14.566 to +1.176/-18.727', breadth_cost='none', falsifier='a second tick capture on UK100/GER40 outside 2026-06-18..07-24 showing hours 00-05 at the modelled 0.87'),
  dict(rank=2, change='ex-ante cost veto: refuse any candidate whose generation-time cost_r exceeds the OOS 25th percentile', saves_R_per_month=float(0.182*len(r)/5), detail='pool: net -0.232 -> -0.050 R/fill, cost 0.213 -> 0.045, pre-cost gross UNCHANGED (-0.019 -> -0.006, CIs overlap)', breadth_cost='87.5% of fills at p25, 75.7% at median', falsifier='a month in which cheap-half net is worse than expensive-half net; has not happened in any of the five'),
  dict(rank=3, change='favourable-carry side only (per symbol, the side that pays no swap)', saves_R_per_month=float(0.0584*len(r)/5), detail='swap 0.0666 -> 0.0143 R/fill; cost 0.2423 -> 0.1839; pre-cost gross -0.0230 -> -0.0145 (BETTER, within noise)', breadth_cost='49.7% of fills', falsifier='a symbol whose adverse-carry side carries a gross edge exceeding its swap; none found at n=146,745'),
  dict(rank=4, change='drop UTC hours 16-21', saves_R_per_month=float(0.0254*len(r)/5), detail='cost 0.2133 -> 0.1906; hour 21 alone costs 0.9216 R/fill and gaps stops by 0.93 R', breadth_cost='13.6% of fills', falsifier='none — hour 21 cost is 4.3x the median hour and is measured on both the model and the tape'),
  dict(rank=5, change='route BTCUSD/ETHUSD commission: FTMO BTCUSD relative spread is 1/19.7 of redacted_account', saves_R_per_month='commission is 38.0% of all cost (11,897 R of 31,303 R); BTCUSD alone is 4,161 R at 0.3984 R/fill', breadth_cost='none if the instrument stays, it is a venue choice', falsifier='a commission schedule change on either host'),
  dict(rank=6, change='raise the modelled slippage from the flat 0.02 to the measured stop-conditional value', saves_R_per_month='0.0 (accounting repair) — it makes published net WORSE by >=0.0117 R/fill', breadth_cost='none', falsifier='a tick capture showing stop gaps below 0.02 R')],
 headline_question=dict(q='what is the five-month record under the full cost-minimal policy, and does any month turn positive?',
   a='NO. At the tightest rung the pool goes from -0.232 to -0.034 R/fill (85% of the loss removed) and every one of the five months stays negative (-0.0085, -0.0954, -0.0456, -0.0052, -0.0241). Pre-cost gross at that rung is +0.00215 +/- 0.0206 — statistically zero. Cost reduction removes the loss asymptotically to zero; it cannot manufacture a gain that is not there.'))
json.dump(H, open(f'{OUT}/H_PROGRAM_AND_HEADLINE_V1.json','w'), indent=1)
print('G,H written')
