import json,os,statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
R=json.load(open(f'{D}/e2_RESULT.json')); MO=['JAN','FEB','MAR','APR','MAY']
C=R['COMPOSITION']
o=[];A=o.append
A("\n---\n\n## 7. NEW FINDING E2-N4 — the born_past_stop artifact is ONE family's generator defect, in every month\n")
A("W0-capture found 3,516 January rows (12.72%) emitted with the stop already breached, \"98.61% one family\".")
A("Measured in all five months, within-family:\n")
ps=C['past_stop_rate_by_family']
fams=[f for f in ps['JAN'] if f!='__POOL__']
A("| family | JAN | FEB | MAR | APR | MAY |\n|---|---:|---:|---:|---:|---:|")
for f in sorted(fams,key=lambda f:-ps['JAN'].get(f,0)):
    A(f"| {f} | {100*ps['JAN'].get(f,0):.2f}% | {100*ps['FEB'].get(f,0):.2f}% | {100*ps['MAR'].get(f,0):.2f}% | {100*ps['APR'].get(f,0):.2f}% | {100*ps['MAY'].get(f,0):.2f}% |")
A(f"| **pool** | {100*ps['JAN']['__POOL__']:.2f}% | {100*ps['FEB']['__POOL__']:.2f}% | {100*ps['MAR']['__POOL__']:.2f}% | {100*ps['APR']['__POOL__']:.2f}% | {100*ps['MAY']['__POOL__']:.2f}% |")
cf=C['past_stop_share_reweighted_to_JAN_family_mix']
A(f"| **pool, reweighted to JAN family mix** | {100*cf['JAN']:.2f}% | {100*cf['FEB']:.2f}% | {100*cf['MAR']:.2f}% | {100*cf['APR']:.2f}% | {100*cf['MAY']:.2f}% |")
A("\n**Two things fall out.**\n")
A("1. **It is a `current_breaker_re_entry` generator defect, not a pool-wide phenomenon.** That family runs")
A("   45.9%-81.8% past-stop in every month; seven of the other nine families run **exactly 0.00% in every")
A("   month**. The defect is structural and monthly-persistent, which strengthens W0-capture's finding")
A("   rather than qualifying it.\n")
A("2. **March's low 5.76% is mostly composition, not a different engine.** March's")
A("   `current_breaker_re_entry` share is 8.06% against January's 15.41%. Reweighted to January's family")
A("   mix March reads 10.86% against January's 12.72% — so composition explains most of the gap and the")
A("   remainder is a lower within-family rate (69.4% vs 81.4%). Pool-level past-stop shares are NOT")
A("   comparable across months without this reweighting.\n")
A("3. **FEBRUARY IS THE ANOMALY and it is new information about the estate's used-once VAL month.**")
A("   February is the ONLY month where the defect leaks outside `current_breaker_re_entry`:")
A("   `current_fvg_fill` 23.20% and `current_ob_retest` 36.97% past-stop, against 0.00% and ~3.2-3.6% in")
A("   every other month — while `current_breaker_re_entry` itself is unusually LOW at 45.94%. Any February")
A("   result conditioned on those two families is measuring a different population from the same result in")
A("   any other month.\n")
A("### 7.1 Family composition of the pool, for anyone pooling months\n")
fs=C['family_share']
A("| family | JAN | FEB | MAR | APR | MAY |\n|---|---:|---:|---:|---:|---:|")
for f in sorted(fams,key=lambda f:-fs['JAN'].get(f,0)):
    A(f"| {f} | {fs['JAN'].get(f,0):.4f} | {fs['FEB'].get(f,0):.4f} | {fs['MAR'].get(f,0):.4f} | {fs['APR'].get(f,0):.4f} | {fs['MAY'].get(f,0):.4f} |")
A("\n---\n\n## 8. WHAT WOULD MAKE THIS BANKABLE\n")
A("Stated as specific evidence requirements, in the order that closes the most uncertainty per unit of cost.\n")
A("**B1 — a month-matched spread series. This is the single largest open error bar and it is cheap.**")
A("Every `real cost` number in this lane and in l10 uses ONE per-symbol median spread in bps measured on the")
A("FTMO tick archive **2026-06-18..07-24**, applied to January-May 2026 rows. The tick archive at")
A("`/Users/borr/GTOSActive/vps-ticks-20260726/` covers only 2026-06-18..07-24 (263,894,769 rows), so no")
A("month in this lane has its own measured spread. The real-cost level could be wrong by the ratio of")
A("June-July spreads to January-May spreads, and that ratio is unmeasured. Nothing here changes SIGN under")
A("plausible error — the pool would have to be 2-3x cheaper than modelled for any book to cross zero — but")
A("the +0.28 lever price and the +0.0036 cell net are both inside that band. **Requirement: a per-symbol")
A("spread series for 2026-01..05, from broker tick data or a bar-level bid/ask capture.**\n")
A("**B2 — the fill contract, which this instrument does not model at all.** Every number here is fill-blind")
A("`gross_r` per W0-F2: 55.2% of \"target-first\" January paths reach +2R before `entry_price` is ever traded.")
A("W0 measured that requiring the fill moves the pool from +0.0409 to -0.2367 on a first-touch contract. The")
A("cheapest families are also the ones with the widest risk distance relative to price, so they are")
A("plausibly the LEAST affected — but that is a hypothesis, not a measurement. **Requirement: re-run the")
A("Section 4 ladder and the Section 6 cell under `w0_ws.walk(require_fill=True)`, all five months.** This is")
A("the highest-value next test in the lane and it needs no new data.\n")
A("**B3 — the cell at n that can carry a decision.** The best cell is 390 rows over five months (78/month,")
A("47 in its thinnest month). Its two families are 1.07% and 2.19% of the pool. At the estate's ratified")
A("standard (`CANDIDATE_BOOK_V1`, all-declared basis, `B_balanced` alpha 0.10) it cannot be evaluated at")
A("this n. **Requirement: either more months (Jun-Dec 2026 packs do not exist), or a relaxation of the cell")
A("to the point where n/month exceeds ~300 while keeping positive mean gross — the K3/london cell")
A("(n>=306/month) is the nearest candidate and it is gross-positive in 3 of 5 months at mean +0.0063.**\n")
A("**B4 — the 2-hour wall.** Every path in this substrate is capped at 120 M1 bars")
A("(`REPAIRED_PENDING_EXPIRY_MINUTES=120`), and W0-capture measured that continuing marked trades into raw")
A("M1 for 24 h is worth +0.017 R/filled trade. `regime_transition_break` and")
A("`volatility_compression_expansion` are the two families whose exits are least likely to be resolved")
A("inside 2 h. **Requirement: extend the winning cell's paths past the wall with the same no-look-ahead")
A("anchor discipline used here.**\n")
A("**B5 — the gate mis-ranking, priced against the LIVE book rather than the pool.** Section 3 shows the")
A("frozen gate mis-ranks on 35-45% of candidates. That gate is live")
A("(`broker_net_cost_engine.py:859-866` spread limb, `:923-927` total limb, thresholds at")
A("`config/agent_config.yaml:715-716`). Its correction is a config/engine change with a decision-contract")
A("consequence (H1). **Requirement: the same frozen-vs-real confusion matrix computed on the sleeves the")
A("live book actually runs, not on the broad V4 pool — that is the version of this number Borhen can act")
A("on.**\n")
A("\n---\n\n## 9. EVIDENCE SPEND REGISTER — declared honestly\n")
sp=R['EVIDENCE_SPEND_REGISTER']
for k in ['APRIL_2026','MAY_2026','MARCH_2026','FEBRUARY_2026']:
    A(f"- **{k}** — {sp[k]}")
A(f"\n**Claim class: {sp['claim_class']}**\n")
A("The protective property worth stating precisely: **every family set, symbol set, session set and gate")
A("threshold evaluated in Sections 4-6 was fixed by JANUARY real cost — a quantity that contains no")
A("outcome — before any April or May row was opened.** April and May were used to MEASURE a")
A("pre-specified structure, not to search for one. The only search in this lane is the 100-cell sweep in")
A("Section 6, and its look count is declared in the artifact itself")
A("(`E2_SWEEP_V1.json -> look_declaration`).\n")
A("\n---\n\n## 10. ARTIFACTS\n")
A("| file | what |\n|---|---|")
for f,w in [('e2_RESULT.md','this receipt'),('e2_RESULT.json','every number above, machine-readable'),
 ('E2_JAN_REPRO_V1.json','60/60 reproduction, both paths'),('E2_FIVE_MONTHS_V1.json','full books, five months'),
 ('E2_MONTHS_ANCHORED_V1.json','four-month anchored books'),('E2_MONTHS_NOANCHOR_V1.json','four-month A-book, no anchor'),
 ('E2_SCALE_VS_RANK_V1.json','scale-vs-rank, four months'),('E2_DECOMP_V1.json','lever stages + scale/rank five months + symbol/session boundary'),
 ('E2_BOUNDARY_V1.json','cross-month family/symbol Spearman tables'),('E2_LEVER_PRICE_V1.json','January-selected K-ladder, all months'),
 ('E2_BEST_CELL_V1.json','gate-fix value + named conditioned cells'),('E2_SWEEP_V1.json','100 declared cells with the look declaration'),
 ('E2_CELLSTAT_V1.json','bootstrap + permutation on the winning cell'),('E2_COMPOSITION_V1.json','family mix and past-stop rate by month'),
 ('E2_MARCH_EXTRACT_V1.json','March pool construction receipt'),('E2_SCHEMA_V1.json','pool schema diff across months'),
 ('e2_MARCH_R0_POOL_V1.jsonl.gz','the March pool this lane built (26,500 rows)'),
 ('e2_ANCHOR_{JAN,FEB,MAR,APR,MAY}.jsonl.gz','zero-look-ahead decision anchors, one per month'),
 ('e2_scripts/e2_recost.py','the portable cost instrument'),('e2_scripts/e2_02_anchor.py','the portable anchor builder'),
 ('e2_scripts/e2_01..e2_19','every measurement script, in order')]:
    A(f"| `{f}` | {w} |")
open(f'{D}/e2_RESULT_part4.md','w').write("\n".join(o)); print('part4 lines',len(o))
