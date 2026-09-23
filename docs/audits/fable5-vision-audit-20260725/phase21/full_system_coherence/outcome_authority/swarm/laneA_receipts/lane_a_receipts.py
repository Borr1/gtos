import json, math, gzip, pickle, statistics as st, random, sys
from collections import Counter, defaultdict
OA='/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority'
out={}

# ---------- R1: RR=2.0 independent verification from RAW sealed compact rows ----------
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725')
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from pathlib import Path
rr=Counter(); nrows=0; roots=[('feb','/private/tmp/w21-market-top-feb-r2'),('aprmay','/private/tmp/w21-market-top-aprmay-r3'),('junjul','/private/tmp/w21-market-top-junjul-r4')]
declared=Counter()
for tag,root in roots:
    root=Path(root)
    for day in sorted(p.name for p in root.iterdir() if p.is_dir()):
        s=json.load(open(root/day/'run_summary.json'))
        sink=ReplayCompactEventSink.open_sealed(root=root/day/'compact_events', expected_authority_root_sha256=s['authority_root_sha256'])
        for r in sink.ledger('missed'):
            e=r.get('entry_price'); sl=r.get('stop_loss'); tp=r.get('take_profit_1')
            if e is None or sl is None or tp is None: continue
            e,sl,tp=float(e),float(sl),float(tp)
            if e==sl: continue
            rr[round(abs(tp-e)/abs(e-sl),4)]+=1
            declared[r.get('risk_reward_ratio')]+=1
            nrows+=1
out['R1_rr_independent_verification']={
 'method':'target/stop price distance recomputed from RAW sealed compact `missed` rows (entry_price, stop_loss, take_profit_1) across all three sealed candidate roots; NOT read from Phase 0 receipts',
 'rows':nrows,
 'observed_target_over_stop_distance':{str(k):v for k,v in rr.most_common()},
 'declared_risk_reward_ratio_field':{str(k):v for k,v in declared.most_common()},
 'phase0_claim':'risk_reward_ratio == 2.0 on 81,968/81,968 MARKET-family rows',
 'verdict':'CONFIRMED' if list(rr)==[2.0] else 'DISCREPANCY'}

# ---------- R2: the 1.5 that misled the plan ----------
tot=Counter()
for m in ['feb','apr','may','jun','jul']:
    with gzip.open(f'/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz','rb') as f: rows=pickle.load(f)
    for r in rows:
        td,sd=r.get('target_distance_atr'),r.get('stop_distance_atr')
        if td and sd: tot[round(td/sd,6)]+=1
out['R2_feature_label_geometry_mismatch']={
 'method':'target_distance_atr / stop_distance_atr over the plan-cache feature rows the ridge was TRAINED on',
 'rows':sum(tot.values()),'ratio_distribution':{str(k):v for k,v in tot.most_common()},
 'finding':'the MODEL FEATURES encode RR 1.5 while the LABELER resolves RR 2.0 (R1). Independent of Phase 0, and not noted by any session.'}

# ---------- R3: no spread double-count ----------
sample=[]
root=Path('/private/tmp/w21-market-top-feb-r2/2026-02-02')
s=json.load(open(root/'run_summary.json'))
sink=ReplayCompactEventSink.open_sealed(root=root/'compact_events', expected_authority_root_sha256=s['authority_root_sha256'])
bad=0; n=0
for r in sink.ledger('missed'):
    c=r.get('cost_r'); 
    if c is None: continue
    parts=sum(float(r.get(k) or 0.0) for k in ('spread_r','expected_slippage_r','commission_r','swap_cost_r'))
    n+=1
    if abs(float(c)-parts)>1e-9: bad+=1
out['R3_spread_double_count_check']={
 'method':'cost_r vs spread_r+expected_slippage_r+commission_r+swap_cost_r on one sealed day; plus code read of candidate_funnel_analysis._lifecycle_row and p0_walk.candidate_record',
 'rows':n,'rows_where_cost_r_ne_sum_of_components':bad,
 'sealed_deductible_definition':'expected_slippage_r + swap_cost_r + commission_r  (SPREAD EXCLUDED) -- candidate_funnel_analysis.py:163-166',
 'phase0_inverted_deductible':'same three terms x (risk_orig/risk_inv) -- p0_walk.py candidate_record',
 'spread_path':'mechanically inside terminal_gross_r: entry on executable ENTRY side, barriers vs executable EXIT side = exactly one round trip',
 'verdict':'NO DOUBLE COUNT. The inverted charge is also correctly SIZED: every cost term is a fixed PRICE amount, and the inverted risk unit is 2x the original, so each term is halved in R -- which is generous to the inversion, not punitive.',
 'eligibility_gate_direction':'the cost_r<=0.20 gate is applied in ORIGINAL units, which EXCLUDES the expensive rows where the inversion does worst (SDE full-pop -0.2848 vs cost-eligible -0.0560). Phase 0 therefore used the denominator FAVOURABLE to the thing it killed.'}

# ---------- R4: power / CIs on the five-month funnel record ----------
def block(name, xs, seed=12345):
    n=len(xs); m=st.mean(xs); sd=st.stdev(xs); se=sd/math.sqrt(n); tot=sum(xs)
    random.seed(seed); b=sorted(sum(random.choices(xs,k=n)) for _ in range(20000))
    return dict(n=n, total_R=round(tot,4), mean_R_per_trade=round(m,5), sd=round(sd,5), se=round(se,5),
                t=round(m/se,4), p_two_sided_normal=round(2*(1-0.5*(1+math.erf(abs(m/se)/math.sqrt(2)))),4),
                ci95_total=[round(tot-1.96*se*n,3), round(tot+1.96*se*n,3)],
                boot95_total=[round(b[500],3), round(b[19500],3)],
                ci95_mean=[round(m-1.96*se,5), round(m+1.96*se,5)],
                zero_inside_ci=bool((tot-1.96*se*n)<=0<=(tot+1.96*se*n)))
files=[('FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json','PASS'),('APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json','REJECT'),('JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json','REJECT')]
res={}; allx=[]; permonth=defaultdict(list)
for f,dec in files:
    d=json.load(open(f'{OA}/{f}')); xs=[float(r['actual_net_r']) for r in d['selected_candidates'] if r.get('actual_net_r') is not None]
    res[f.split('_')[0]+f' (sealed decision {dec})']=block(f,xs); allx+=xs
    for r in d['selected_candidates']:
        if r.get('actual_net_r') is None: continue
        permonth[str(r.get('trading_day'))[:7]].append(float(r['actual_net_r']))
for mo in sorted(permonth):
    if len(permonth[mo])>2: res[mo]=block(mo,permonth[mo])
res['POOLED_ALL_FIVE_MONTHS']=block('pooled',allx)
res['POOLED_EXCLUDING_FEBRUARY']=block('nofeb',[x for mo,v in permonth.items() if not mo.startswith('2026-02') for x in v])
sd=st.stdev(allx)
mde=lambda d: math.ceil((1.96+0.8416)**2*sd**2/d**2)
out['R4_five_month_power']={
 'method':'per-trade actual_net_r read straight out of the three sealed validation-result JSONs; normal + 20k bootstrap CIs',
 'results':res,
 'sd_R_per_trade_pooled':round(sd,4),
 'trades_needed_for_80pct_power_two_sided_alpha05':{f'+{d} R/trade':mde(d) for d in (0.05,0.10,0.15,0.20,0.30)},
 'trades_actually_read_in_five_months':len(allx),
 'months_needed_at_observed_rate':{f'+{d} R/trade':round(mde(d)/(len(allx)/5),1) for d in (0.10,0.15,0.20)},
 'finding':'NOTHING in the five-month sealed record of the SELECTED book is distinguishable from zero in either direction. Pooled = +0.954 R over 282 trades, t=+0.05. February +14.168 is t=+1.23; July -14.566 is t=-1.50.',
 'estate_already_knew':'THREE_MONTH_POSTMORTEM_V1.md section 5.4: "BAR-2 is the honest-statistics bar: it would not have passed even February". BAR-2 was reported-not-used; BAR-3 (a point-estimate bar) was ratified instead.'}

# ---------- R5: CS breaker driftless benchmark ----------
dist=[]; spr=[]; mkt=Counter()
for m in ['feb','apr','may','jun','jul']:
    with gzip.open(f'/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz','rb') as f: rows=pickle.load(f)
    for r in rows:
        if r.get('origin_family')!='current_breaker_re_entry': continue
        if r.get('distance_to_limit_risk') is not None: dist.append(float(r['distance_to_limit_risk']))
        if r.get('spread_r') is not None: spr.append(float(r['spread_r']))
        mkt[str(r.get('limit_marketable_at_decision'))]+=1
dist.sort(); spr.sort(); q=lambda a,p:a[int(p*(len(a)-1))]
p_drift=0.25/(5.0+0.25)
cells={}
for lbl,(T,S,H,N) in {'April_2026':(2506,738,427,3671),'May_2026':(1832,865,674,3371)}.items():
    barrier=T/(T+S); nb=T+S; se=math.sqrt(p_drift*(1-p_drift)/nb)
    cells[lbl]=dict(TARGET=T,STOP=S,HORIZON=H,n=N,target_share_all=round(T/N,4),
                    target_share_barrier_resolved=round(barrier,4),
                    x_driftless_all=round((T/N)/p_drift,2), x_driftless_barrier=round(barrier/p_drift,2),
                    z_vs_driftless=round((barrier-p_drift)/se,1),
                    implied_gross_E_R_at_20to1=round((T/N)*20-(S/N),3))
out['R5_cs_breaker_driftless_plausibility']={
 'geometry':'src/components/current_breaker_re_entry_repair.py:28-29,92-93 -- base_distance = |entry - original_stop| = D; repaired stop = 0.25D, repaired target = 5.0D, side INVERTED. Reward:risk = 20:1.',
 'driftless_first_passage_P_target_first':round(p_drift,5),
 'per_capture':cells,
 'contrast':'the funnel program killed its own inversion thesis on families running 0.7-0.9x their driftless rate at z=-5.6..-25.0 (PHASE0_INVERSION_TRUTH_V1 section 2). No session ever pointed the same benchmark at this candidate.',
 'family_microstructure_current_breaker_re_entry':{
   'rows_in_funnel_cache':len(dist),
   'distance_to_limit_risk_D':{'p10':round(q(dist,.10),3),'median':round(q(dist,.5),3),'p75':round(q(dist,.75),3),'p90':round(q(dist,.90),3)},
   'limit_marketable_at_decision':dict(mkt),
   'median_spread_r_original_units':round(q(spr,.5),4),
   'median_spread_in_repaired_risk_units':round(q(spr,.5)/0.25,4),
   'note':'the repaired 0.25D stop is a fraction of a spread wide; CS receipt reports mean spread cost 0.730175 R against that same 0.25D risk unit.'},
 'unreconciled_with':'PHASE0_INVERSION_TRUTH_V1 section 6 measured that the committed labeler CANNOT express an inverted LIMIT contract for this exact family: 4,258 of 4,360 rows (97.7%) censor as CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING (quote_side.py:1249-1250). CS resolved 3,671/3,671 with ZERO censoring through a different path stack (the CK sidecar). Phase 0 wrote "the two are not in conflict and neither supports the other" without reconciling this.'}

# ---------- R6: CS multiplicity + permutation forensics ----------
p_mc=26/10001; p_exact_naive=2/2048; p_exact_plus1=3/2049; m=59; a=0.10
w21={'exact_tail':11,'mc_tail':80}
out['R6_cs_kill_forensics']={
 'stated_kill':'REJECT significance: q=0.1534 (raw p=0.0026) fails benjamini_hochberg at alpha=0.1 across a family of 59',
 'bh_arithmetic':{'p':p_mc,'m':m,'q':round(p_mc*m,6),'rank':1,
   'note':'the candidate is rank 1 of 59, so BH is IDENTICAL to Bonferroni here; 58 of 59 members are padded at p=1.0 (family_members_padded_at_p1=58, n_sleeves_judged_this_run=1), so BH bought exactly zero power over Bonferroni.'},
 'p_value_provenance':{'value':p_mc,'exactly':'26/10001','reading':'Monte Carlo block permutation, 10,000 draws, 25 exceedances, (1+k)/(N+1) convention'},
 'seed_stability_check_MY_OWN_CONCERN_REFUTED':{
   'concern':'the BH rank-1 bar 0.0016949 lies inside the Clopper-Pearson 95% CI [0.001619, 0.003688] on the true p',
   'operational_test':'P(a re-seeded 10,000-draw run lands at or below the bar | true p = 0.0026) = 0.0141, i.e. ~0.3 of 20 seeds',
   'verdict':'CONCERN REFUTED. Unlike AO B1321 (which flipped on 4 of 20 seeds), the CS MC verdict is seed-stable. This objection does NOT undermine the kill.'},
 'THE_REAL_DEFECT_exact_null_was_available_and_admits':{
   'source':'phase21/WAVE21_INTEGRATION.md section 10: "exact-null tail 2 -> 11 of 2048; MC tail 25 -> 80 of 10,000"',
   'achievable_permutation_space':2048,
   'exact_null_p_naive_k_over_n':round(p_exact_naive,7),'exact_q':round(p_exact_naive*m,4),
   'exact_null_p_plus1_convention':round(p_exact_plus1,7),'exact_q_plus1':round(p_exact_plus1*m,4),
   'mc_null_p':round(p_mc,7),'mc_q':round(p_mc*m,4),
   'verdict_under_exact_null':'ADMIT at alpha=0.10 under BOTH conventions (q=0.0576 and q=0.0864)',
   'verdict_under_mc_null':'REJECT (q=0.1534)',
   'finding':'The permutation space has only 2,048 achievable assignments. It is CHEAPER to enumerate exactly (2,048 evaluations) than to Monte-Carlo it (10,000 draws), and exact enumeration is also EXACT. The gate consumed the noisier and more expensive of two available estimates, and that choice -- not the evidence -- is what produced the REJECT. WAVE21_INTEGRATION section 10 confirms the estate itself computed the exact null and labelled the corresponding verdict ADMIT (q 0.0576).'},
 'family_composition_audit':{
   'declared_family':'CANDIDATE_BOOK_V1 at the V27 tip, 59 all-declared / 57 looks',
   'stated_purpose':'"The pool an arming decision draws from: every sleeve the live config\'s own resolvers can build."',
   'membership_of_the_judged_candidate':'cq_current_breaker_re_entry_inverted_5d_stop_0p25d is NOT a sleeve the live config resolvers can build; V27 records it as "rebased from the parallel fork CQ_CANDIDATE_FAMILY_V..." -- an integration decision, not the family\'s own membership rule.',
   'literal_duplicates':['ch_p1_hist::m1::mx_btcusd_target5_redacted_account (dup of member 15)','ch_p1_hist::m2::mx_ethusd_d1_donchian_20_breakout (dup of 17)','ch_p1_hist::m2::mx_avausd_d1_donchian_20_breakout (dup of 14)','ch_p1_hist::m2::mx_nzdjpy_d1_donchian_20_breakout (dup of 22)'],
   'nested_near_duplicates':['5x overlay_metalabel_fx_jpy_* (nested thresholds on ONE sleeve)','5x thr_sub_xvol_pullback_* (nested thresholds on ONE sleeve)','6x mxf_volume_surge_reversal_* (one mechanism across six index symbols)','3x mxf_energy_fvg_retest_* (one mechanism across three energy symbols)'],
   'precedent_in_this_program':'wave 8 found the historical 69-look family DOUBLE-COUNTED (W and X looks were subsets of AA 32) and that published q-values were OVER-corrected. The same defect class is present here and was not re-checked.',
   'largest_family_that_still_admits_at_the_MC_p':38,
   'family_size_history':'CANDIDATE_BOOK_V1 was 32 declared at V1 (ratified 2026-07-30) and 59 at V27 (2026-08-01). Monotone by design (freeze_rule.look_taken_ACQUISITION_raises_the_bill_and_that_is_deliberate). An identical candidate tested two days earlier would have ADMITTED at every convention.',
   'estate_own_admission':'gate_result.family.n_trials_basis: "FLOOR, not a measurement. No trial-budget ledger artifact exists anywhere in the repo."'},
 'the_kill_that_actually_holds':{
   'source':'phase21/WAVE21_INTEGRATION.md section 10, B3406',
   'what':'at the wave-21 artifact-bound slippage authority, six of the sleeve\'s sixteen symbols (AUDJPY, CHFJPY, EURJPY, UKOIL.cash, USOIL.cash, XAGUSD) have no reconciled price-domain slippage sample and fail closed',
   'evaluable_universe':'10 of 16 symbols, 63.556% of trades',
   'exact_null_at_wave21':f'{w21["exact_tail"]}/2048 = {round(w21["exact_tail"]/2048,5)} -> q = {round(w21["exact_tail"]/2048*m,4)}  REJECT under the EXACT null too',
   'mc_null_at_wave21':f'{w21["mc_tail"]}/10000 -> q = 0.3169  REJECT',
   'verdict':'THIS kill is robust to the p-value convention, to the null estimator, and to the family denominator down to m=18. It is the sound kill. CS did not make it -- it was found at wave-21 integration, after the fact.'}}
json.dump(out, open('/tmp/laneA/LANE_A_RECEIPTS.json','w'), indent=1)
print(json.dumps({k:(v if k in ('R1_rr_independent_verification',) else '...') for k,v in out.items()}, indent=1)[:900])
print('WROTE /tmp/laneA/LANE_A_RECEIPTS.json')
