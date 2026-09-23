"""e1 step 11: assemble E1_RESULT.json from every measured artifact."""
import json
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def L(f): return json.load(open(f'{D}/{f}'))
out={
 'lane':'e1-extend-l10-x5x6',
 'posture':'EXTENSION of l10-broker-truth X5/X6. Reproduce -> mechanism -> five months -> boundary -> bankability.',
 'REPRODUCTION':{
   'verdict':'EXACT',
   'reference':'L10X_POOL_RECOST_V1.json (l10_scripts/l10x_06_recost.py)',
   'reproduced':{'frozen_total_mean':0.663161,'real_total_mean':0.189297,'ratio_total':3.503,
     'ratio_spread':4.520,'gate_frozen_n_pass':7210,'gate_real_n_pass':12629,'pool_gross':-0.217496},
   'independent_min_spread_r':{'SPX500':{'n':1943,'min_frozen_spread_r':0.24479,'n_pass_gate':0},
     'NAS100':{'n':1622,'min_frozen_spread_r':0.16326,'n_pass_gate':0}},
   'per_symbol_pass_counts_match':'24 of 24 symbols reproduce l10 n_pass_frozen exactly',
   'evidence':'E1_JAN_REPRO_INDEP_V1.json; e1_scripts/e1_00_repro_jan.py'},
 'MECHANISM':{
   'headline':'The frozen spread is not a measurement. It is a four-tier config fallback whose fourth tier charges max_spread_cents - a REFUSAL CEILING - as the expected spread.',
   'fallback_chain':[
     {'tier':1,'source':'cached pre-decision tick row','file':'src/research_infra/v4_timewarp_simulated_live_research_loop.py:58760-58795','jan_symbols':['XAUUSD','XAGUSD','BTCUSD','EURUSD','USDJPY']},
     {'tier':2,'source':'TICK_SPREAD_FLOOR_R (a FLOOR in R units, used as the point estimate)','file':'src/components/ultimate_book/admission.py:73-84 ; applied v4_timewarp:58796-58805','jan_symbols':['USOIL_cash (0.0270)','UKOIL_cash (0.0258)','BTCUSD (0.0001)'],'note':'measured constant frozen spread_r exactly equal to the table value in all five months'},
     {'tier':3,'source':'broker profile market.spread x market.point','file':'v4_timewarp:58807-58821 ; config/profiles/ftmo.yaml','jan_symbols':['AUDJPY 11x0.001=0.011','GBPJPY 18x0.001=0.018','FX majors 5e-5..1e-4']},
     {'tier':4,'source':'max_spread_cents / 100  <-- CEILING CHARGED AS ESTIMATE','file':'v4_timewarp:58822-58832 ; config/agent_config.yaml','jan_symbols':['NAS100','SPX500','JP225','UK100','GER40','US30_cash','ETHUSD','EURJPY','CHFJPY']}],
   'config_ceilings_and_line_numbers':{
     'NAS100':{'line':4430,'max_spread_cents':5000,'charged_px':50.0,'comment':'50 pts: (ask-bid)*100 convention'},
     'JP225':{'line':5010,'max_spread_cents':5000,'charged_px':50.0},
     'SPX500':{'line':5036,'max_spread_cents':1000,'charged_px':10.0},
     'ETHUSD':{'line':4927,'max_spread_cents':1000,'charged_px':10.0},
     'US30_cash':{'line':4706,'max_spread_cents':800,'charged_px':8.0,'comment':'8 pts ... Typical ~2 pts -> 200'},
     'UK100':{'line':4472,'max_spread_cents':500,'charged_px':5.0,'comment':'5 pts ... typical 1 pt, p99 4 pts'},
     'GER40':{'line':4514,'max_spread_cents':500,'charged_px':5.0},
     'EURJPY':{'line':4982,'max_spread_cents':5.0,'charged_px':0.05},
     'CHFJPY':{'line':4901,'max_spread_cents':5.0,'charged_px':0.05}},
   'self_indicting_comments':'config/agent_config.yaml:4706 declares "Typical ~2 pts -> 200" beside the 800 it charges (4x); :4472 declares "typical 1 pt, p99 4 pts" beside the 500 it charges (5x). The config records the right answer on the same line as the wrong one.',
   'proof':'implied frozen spread in price units is EXACTLY constant (coefficient of variation < 1e-9) and EXACTLY equal to max_spread_cents/100 for all nine symbols, in all five months.',
   'irony':'Both safety rails are wired into the expectation and each is wrong in its own direction: the REFUSAL CEILING (tier 4) becomes the estimate and over-charges 2.0-29.3x; the NEVER-CHEAPER-THAN FLOOR (tier 2) becomes the estimate and under-charges the January oils to 0.28-0.38x.'},
 'MONTHS':L('E1_MONTHS_V1.json'),
 'ERATRUE':L('E1_ERATRUE_RECOST_V1.json'),
 'FULL_LEDGER_ERATRUE':L('E1_FULLLEDGER_ERATRUE_V1.json'),
 'SELECTION_ON_ERROR':L('E1_SELECTION_ON_ERROR_V1.json'),
 'BOUNDARY':L('E1_BOUNDARY_V1.json'),
 'STOPWIDTH':L('E1_STOPWIDTH_V1.json'),
 'PASTSTOP_CONTROL':L('E1_CONTROL_PASTSTOP_V2.json'),
 'RESTORED_GRID':L('E1_RESTORED_GRID_V1.json'),
 'ERA_SPREAD_TABLE':L('E1_ERA_SPREAD_V1.json'),
 'ECONOMICS_SPEND_REGISTER':{
   'windows_spent':['APRIL 2026 (CS_APRIL_S0R0_V2)','MAY 2026 (CS_MAY_S0R0_V1)'],
   'what_was_read':'opportunity_net_proxy_r on the diagnostic pool only (25,056 April rows / 21,285 May rows), used for exactly four aggregates per month: pool gross mean, gross mean of the frozen-gate-passed set, gross mean of the real-cost-gate-passed set, gross mean of the newly admitted set; plus the 36-cell pre-declared restored-universe grid and the stop-width decile table.',
   'what_was_NOT_read':'no per-trade selection, no rule fitted on April or May, no arm scored, no candidate promoted. The FULL-LEDGER pass (E1_FULLLEDGER_ERATRUE_V1.json) reads ZERO economics - opportunity_net_proxy_r is null on all 82% of the ledger outside the pool.',
   'april_values':{'pool_gross':-0.2319,'gross_pass_frozen':-0.1070,'gross_pass_real':-0.1623,'gross_newly_admitted':-0.1959},
   'may_values':{'pool_gross':-0.2387,'gross_pass_frozen':-0.1415,'gross_pass_real':-0.1240,'gross_newly_admitted':-0.1227},
   'verdict':'both months agree with January/February/March: the restored universe is gross-negative. No economics-bearing decision was taken on either window.'},
 'BANKABILITY':{
   'what_is_already_bankable':'The mechanism. The frozen spread for nine symbols is a config refusal ceiling, provable from source and config with no new data, and confirmed by a second independent instrument (src/costs/spread_model.py era-true, MEASURED coverage for 7 of the 9).',
   'what_is_NOT_bankable':'That correcting it earns money. The rows it restores are gross -0.030 to -0.124 R and net -0.105 to -0.197 R at real cost, in all five months. No pre-declared cell of the restored universe is positive in 5/5 months.',
   'evidence_needed_to_put_money_behind_it':[
     '1. A SELECTOR over the restored universe. The repair hands back 38,619-56,079 ledger rows/month (+157% to +281%); the binding question is now whether anything separates them. That is a walk-forward selection problem on data that already exists - no new replay.',
     '2. The 0.10/0.15 caps re-derived at era-true cost. They were calibrated against a scale 3-6x too high; at era-true cost the mean pool cost is 0.137-0.227 R, so the 0.15 total cap is now the binding constraint in its own right and has never been justified at the corrected scale.',
     '3. Fill realism on the index complex. W0-F2 measured that 55.2% of target-first paths reach +2R before entry is ever traded. Every number in this receipt is fill-blind; restoring the index complex without a fill contract restores fictitious as well as real value.',
     '4. A sealed replay is NOT required and MUST NOT be the gate. config/agent_config.yaml is R2-bound (H1) so editing the ceilings breaks the seal; but the cost term can be corrected in the pre-trade packet without touching the ceiling keys, because the ceiling is only ever read as a FALLBACK when tier 1-3 miss.']},
}
json.dump(out,open(f'{D}/e1_RESULT.json','w'),indent=1)
print('wrote e1_RESULT.json', len(json.dumps(out)))
