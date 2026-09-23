# January refusal funnel with outcome economics — Session FA, wave-19 broad forensic (2026-08-01)

Mission: the owner's question — *"why did the system leave the positive options and go for the
negative option — is there a reason it was chosen, and the other ones declined?"* — answered over
the January CJ_RECLOCKED_S0R0_V7 arm: full physical funnel census, per-refusal-class outcome
economics, the residual choice set, the cost>1R band, the non-scoreable census, and the
declined-winners attribution.

Sources (all read in place, read-only):
- Full missed ledger (153,425 rows, 1.34 GB, streamed): `wave16-rematerialization-20260731/.../CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl`
- Compact scoreable pool (27,658 rows): `phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`
- Lane trade table (57 executed trades): `phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl`
- Pool receipt: `phase16/receipts/CJ_RECLOCKED_POOL_S0R0_V1.json`

Outputs in this directory: `FUNNEL_CENSUS.json`, `REFUSAL_OUTCOMES.json`,
`RESIDUAL_CHOICE_SET.json`, `COST_BAND_CROSS.json`, `NONSCOREABLE_CENSUS.json`,
`DECLINED_WINNERS.json`, `CLARIFIERS.json`; scripts `census_full_ledger.py`,
`pool_analysis.py`, `clarifiers.py`.

**Cross-check status: every receipt number reconciled exactly** — 153,425 physical; 27,658
scoreable; 7,706 positive; sum net −24,357.1989; mean net −0.880657; mean gross −0.217496; mean
cost 0.663161; 4,908 cost>1R rows; 7,210 cost-executable-true; 57 trades summing −5.5062 R;
21/21 negative scoreable days. Zero deltas.

---

## 1. The stage-ordered waterfall (all 153,425 physical rows)

Stage order was derived from the joint counts, not assumed. The joints that pin it:
`selector_reason x pretrade_cost_packet_status` (every cost-flavored selector reject sits on
REFUSED; every quality reject sits on PASSED), `selector_action x scheduler_materialization_status`
(materialization draws only from specific action/reason combinations), and
`scheduler_materialization_status x scheduler_selection_disposition` (exact partition).

| stage | survivors in | killed here | dominant kill reasons |
|---|---:|---:|---|
| 0. candidates written to missed ledger | 153,425 | — | (57 executed trades + 122 orders live outside this ledger) |
| 1. broker pre-trade cost packet | 153,425 | **128,293 REFUSED (83.6%)** | selector_reason `broker_net_pretrade_cost_packet_refused` 75,145 + `broker_net_admission_ev_negative_after_cost` 53,052 + 96 source-required holds; miss_reason `...cost_failed` = 128,293 exactly |
| 2. selector quality gates (on the 25,132 cost-PASSED) | 25,132 | 14,198 hard rejects | `admission_quality_dynamic_router_refused_candidate_use` 9,200, `numeric_confluence_structured_disagreement` 4,551, `off_configured_session_entry_blocked` 3,384, `no_shadow_sleeve_match` 1,162, `non_admission_sleeve_only` 452 |
| 3. materialization to scheduler | 10,934 selector-passing (reduce 6,641 + open-reduced 4,228 + trade 22 + source-req 43) | 5,985 never ranked (reduce-risk 5,706, open-reduced 140, source-required 139); **+3,536 stage-2 router-rejects re-enter softened** | signed-authority/config gates: `positive_reduce_risk_signed_authority_invalid` 2,942+247, `open_reduced_...disabled_by_config` 1,290+124, `not_new_entry_authority` 783+82, source-required override failures |
| 4. scheduler ranking | **8,581 materialized (5.6% of physical)** | 8,354 `candidate_generated_not_scheduler_selected` | competition for slots + package vetoes (displacement quality 2,075 scoreable-side, fill floor 1,443) |
| 5. risk finalizer on preselected | 227 | 227 `scheduler_preselected_then_rejected_by_finalizer` | marketable_guard 131, fill_realism 77, package_authority 16 |
| 6. selected → orders → trades | 122 orders | — | 57 trades, realized **−5.5062 R** (lane meta counts: missed 153,425 / order 122 / trade 57 confirm) |

Funnel is NOT strictly monotone — two recorded ambiguities:
- 3,536 selector-action=`reject` rows (all reason `admission_quality_dynamic_router_refused_candidate_use`)
  were nonetheless scheduler-materialized: effective action softened to `open-reduced-risk` (204 of the
  207 scoreable ones), i.e. replay materialization of router-refused candidates.
- `final_blocker_class = cost_authority` counts 125,012 while packet REFUSED counts 128,293: 3,281
  non-scoreable REFUSED rows carry a different final blocker (`source_or_signature_authority` etc.).
  On the scoreable side the two are identical (20,448 = 20,448).

## 2. Refusal class vs outcome (scoreable 27,658; net = opportunity_net_proxy_r, gross = net + cost_r)

**Every economically material refusal class refused rows that were, on average, losers.**

| refusal class | n | mean net R | sum net R | mean gross R | pos % | refusal correct on avg? |
|---|---:|---:|---:|---:|---:|---|
| cost_authority (blocker) | 20,448 | −1.121 | −22,923.5 | −0.255 | 23.2 | YES — 94.1% of pool loss |
| `broker_net_admission_ev_negative_after_cost` | 6,453 | −2.326 | −15,006.3 | −0.353 | 11.1 | YES — the single sharpest gate |
| `broker_net_pretrade_cost_packet_refused` | 13,907 | −0.567 | −7,888.2 | −0.211 | 28.7 | YES |
| router refusal materialized-for-replay | 3,743 | −0.214 | −800.9 | −0.128 | 38.7 | YES |
| off-configured-session block | 1,079 | −0.238 | −256.9 | −0.155 | 37.9 | YES |
| package_authority (blocker) | 2,668 | −0.213 | −567.5 | −0.122 | 40.3 | YES |
| scheduler_selection (blocker) | 689 | −0.143 | −98.8 | −0.073 | 44.0 | YES |
| execution_fillability (blocker) | 449 | −0.068 | −30.4 | **+0.027 gross** | 63.0 | marginal — gross-positive, net-negative |
| `numeric_confluence_structured_disagreement` | 484 | −0.020 | −9.6 | **+0.088 gross** | 65.9 | breakeven |
| **daily_lockout (blocker)** | **47** | **+0.242** | **+11.4** | +0.326 | 70.2 | **NO — but trivially small** |
| same_symbol_daily_loss_lockout (finalizer) | 55 | +0.149 | +8.2 | +0.236 | 65.5 | NO — trivially small |

The only gates that refused on-average-positive rows are the two daily-loss lockouts, worth ~+20 R
forgone across the month — noise against −24,357 R avoided. Full tables incl. every
risk_finalizer_reason: `REFUSAL_OUTCOMES.json`.

## 3. The residual choice set — what the scheduler actually chose from

Definition A (cost-executable AND selector pass): **n = 4,509, mean net −0.199 R, 42.3% positive,
sum −895.4 R, mean cost 0.088 R.** Definition B (literally scheduler-ranked): n = 4,095, mean
−0.213, 40.3% positive. Overlap A∩B 3,888; A\B 621 (killed by signed-authority gates, the
*best*-economics refused group: mean −0.092, 58.5% positive — still negative mean); B\A 207 (the
softened router-rejects).

**The choice set itself was negative.** Its best family within B was `regime_transition_break`
(n=37, +0.125) — everything with size was negative: displacement_continuation n=1,636 −0.190,
liquidity_sweep_reclaim n=725 −0.096, current_fvg_fill n=616 −0.254, current_breaker_re_entry
n=232 −0.762. LONG (−0.165) beat SHORT (−0.261); ny (−0.185) beat london/off-session/tokyo.

**What the scheduler selected did BETTER than what it declined:** the 57 executed trades realized
mean −0.100 R/trade (sum −5.506, 41.8% positive) against the declined ranked set's −0.213 proxy
mean. (Caveat: realized final_r under the selected policy replay vs the 2R-policy diagnostic
proxy — directionally comparable, not identical contracts.) The scheduler cannot be convicted of
adverse selection: it faced a 40%-positive, negative-mean menu and picked slightly above its
menu's average.

**Why it picked at all:** the model's own `expected_net_r` was **positive on every quartile of the
ranked set** (+0.675 → +1.197) while realized proxy means were negative in every quartile
(−0.245 → −0.153). An ex-ante optimism bias of ≈ +1 R/row is the reason "the negative option was
chosen": *to the system's own EV model, nothing it ranked looked negative.* The EV ordering
carried weak real signal (Q4 −0.153 / 47.5% pos vs Q1 −0.245 / 38.1%) but the level was wrong by
~1 R everywhere. Scheduler rank itself was uninformative-to-inverted among declined rows: rank-1
−0.236 vs rank-4–10 −0.188.

## 4. The cost>1R band (stop narrower than round-trip cost)

4,908 rows, sum net −13,195.2 R = **54.17% of the whole pool loss** in 17.7% of rows.
**Containment was perfect**: 4,908/4,908 final blocker `cost_authority`, all
cost-executable=false, **0 leaked into the residual set, 0 into the ranked set, 0 executed**
(max executed trade cost_r = 0.1765). The cost gate did exactly its job on the band that
mattered most.

## 5. Non-scoreable census (125,767 rows)

All 125,767 carry `missed_opportunity_r_scoreability_status = path_auditable_r_unscoreable` and a
**null** `opportunity_net_proxy_r` — no outcome information exists in this ledger for them.
107,845 (85.8%) are cost-packet failures; 4,486 were scheduler-materialized yet still unscoreable.
By status name they are *path-auditable*: outcomes are recoverable in principle only by an
ordered-path re-decode (the CQ sidecar covers exactly the 27,658 scoreable ones, not these).
Table: `NONSCOREABLE_CENSUS.json`.

## 6. Declined winners (the owner's question, first pass)

7,706 ex-post winners worth +6,447.2 R (against 19,952 losers worth −30,804.4 R in the same pool):

- **61.4% of winners (4,733, +4,307.7 R) died at cost_authority** — the same gate that avoided
  −27,231.2 R of losers in that class (net −22,923.5 R avoided). Refusing them was correct in
  aggregate; the winners are not separable *by that gate*.
- Top decile (n=2,765, ≥ +1.07 R each, +4,345.4 R): 75.0% died at cost_authority — the biggest
  winners were concentrated exactly where costs said "unexecutable".
- 1,906 winners (+1,445.6 R) DID reach the residual choice set; 1,651 were scheduler-ranked and
  declined. Those 1,651 sat inside a ranked set whose other 2,444 rows sum to −2,192.0 R; no
  signal available to the scheduler at decision time separated them (§3).
- **Class (a) NY-session LONG metals** (XAUUSD/XAGUSD × LONG × ny): 411 rows, class total only
  **+12.75 R** (mean +0.031, 65.2% positive). It was NOT cost-blocked: 317/411 reached the
  residual set; its winners (268, +159.1 R) died mostly at package_authority (65),
  execution_fillability (63) and scheduler_selection (52). The class is real but small: even
  perfect capture of every row was worth ~+13 R net over the month at 2R policy.
- **Class (b) liquidity_sweep_reclaim × LONG**: 1,955 rows, class total **−970.1 R** (mean −0.496).
  Cost authority killed 1,435 rows carrying −951.4 R of it — correctly. The 388 rows that reached
  the residual set were exactly breakeven (mean +0.006). Its 736 winners (+740.6 R) were 67.5%
  cost-refused, i.e. embedded in the same cost-toxic stratum.

## 7. Answer to the owner's question

The January system did **not** identify positive options and decline them in favor of a negative
one. (1) Every gate with economic mass refused row classes that were negative on average — the
funnel *added* value at every material stage, avoiding −24,357 R of diagnostic loss, of which the
cost gate alone avoided −22,923 R with zero leakage of the worst band. (2) By the time anything
reached a genuine *choice*, the entire menu was negative-mean (−0.199 R, 42% positive), and the
scheduler's 57 picks (−0.100 R/trade realized) modestly outperformed what it declined (−0.213).
(3) The reason it traded at all is an ex-ante EV model that priced every ranked candidate as
positive (+0.68 to +1.20 R expected) when reality was −0.15 to −0.25 R — an optimism gap of ≈1 R
per row. The failure is generation-plus-calibration ("everything looks like a winner after my
costs"), not selection ("I picked the loser from a good menu"). (4) The ex-post winners exist
(+6,447 R) but 61–75% of them lived inside cost-refused strata whose aggregate was strongly
negative; the two nameable positive classes were either tiny (+12.7 R total, NY-metals-LONG) or
negative as a class (−970 R, LSR-LONG). Nothing in this funnel had a rule available to it, at
decision time, that separated those winners from their surrounding losers — which is exactly
JANUARY_BANK §3's "separability is open and unmeasured" claim, now given its per-gate accounting.

Caveats: proxy-vs-realized contract mismatch on the executed-vs-declined comparison (§3);
`opportunity_net_proxy_r` is the 2R-policy diagnostic proxy, not a replay; non-scoreable 82% of
physical rows carry no outcome at all (§5), so all economics here are conditional on the
scoreable 18%.
