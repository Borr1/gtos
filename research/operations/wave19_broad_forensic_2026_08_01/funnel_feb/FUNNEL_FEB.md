# February refusal funnel — Session FA wave-19 forensic (funnel_feb)

**Evidence class: FEBRUARY ATTRIBUTION EVIDENCE ONLY.** February re-decode is
owner-authorized (2026-08-01) for defect attribution. Nothing here is a selection
surface; February stays a used-once VAL window.

Sources (raw artifacts, never prose):
- Full arm ledger: `wave18-true-utc-factory-20260801/.../CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl` (1.21 GB, streamed)
- Compact pool: `phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz`
- January reference: `CJ_RECLOCKED_S0R0_V7` ledger (streamed) + `phase16` pool
- Lane trade tables (executed apex): phase18 / phase16 `LANE_TRADE_TABLE.jsonl`

Cross-checks — all reconcile exactly: 129,165 physical rows; 24,239 scoreable;
mean net −0.64002116; mean gross −0.15055128; positive rows 7,498 (30.93%); pool
net −15,513.4728 R; 20/20 scoreable days negative; 58 executed trades summing
−3.96140 R; cost>1.0 band 2,897 rows / 38.774% of pool loss (all match
`CP_FEBRUARY_POOL_S0R0_V1.json`). January side reconciles to its receipt too
(153,425 / 27,658 / −0.88066 / 57 trades −5.50621 with 2 null `net_r` rows).

## 1. Stage-ordered waterfall (all 129,165 physical rows)

Stage model (first-refusal attribution, pipeline order): S1 selector
(`effective_selector_action` in {reject, source-required}) → S2 materialization
skip (`not_scheduler_ranked`) → S3 scheduler decline
(`candidate_generated_not_scheduler_selected`) → S4 finalizer rejection of
preselected. Zero rows are unattributed in either month.

| stage | Feb refused | Feb share | Jan share | Feb scoreable econ (mean net / pos share) |
|---|---:|---:|---:|---|
| S1 selector | 120,890 | 93.59% | 91.24% | −0.698 / 29.2% (n=21,608) |
| S2 materialization | 3,799 | 2.94% | 3.82% | −0.281 / 44.3% (n=687) |
| S3 scheduler select | 4,464 | 3.46% | 4.92% | −0.121 / 45.0% (n=1,935) |
| S4 risk finalizer | 12 | 0.01% | 0.01% | −0.186 / 55.6% (n=9) |
| executed (lane, not in ledger) | 58 trades | — | 57 | −3.961 R realized |

The funnel *shape* is stable month over month; February leans ~2.3 pp harder on
the selector. Full detail: `STAGE_WATERFALL.json`, `FUNNEL_CENSUS.json`.

## 2. Refusal vs outcome — every gate was economically correct in February

All 11 selector reasons, all final-blocker classes, all finalizer reasons refuse
row-sets with negative mean net proxy (`REFUSAL_OUTCOMES.json`,
`refusal_economically_correct_on_average` = true on every group). The two big
cost gates: `broker_net_pretrade_cost_packet_refused` n=15,770 at −0.478 mean
net; `broker_net_admission_ev_negative_after_cost` n=4,104 at −1.783. Softest
gates (`no_shadow_sleeve_match` −0.069, `non_admission_sleeve_only` −0.027,
gross means slightly positive) still refuse net-negative row-sets. January was
qualitatively identical; the marginal January cells (S2 gross +0.003, S4 70%
positive on n=10) went negative in February — no gate got *less* correct.

## 3. Residual choice set — shrank 41% and stayed far below breakeven

Definition: selector risk-bearing AND `scheduler_option_materialized`.
Feb: 4,476 physical / 1,944 scoreable — vs Jan 7,575 / 3,242.
Economics: mean net −0.121, mean gross −0.031, positive share 45.0% against the
60.6% breakeven precision. Composition is ob_retest-dominated (top cells:
ob_retest SHORT london 321, SHORT ny 280, LONG london 209, LONG ny 202).
Scheduler-declined (n=1,935, −0.121) vs preselected-then-finalizer-rejected
(n=9, −0.186): no evidence the scheduler was discarding better rows than it
kept — and the executed apex (58 trades) realized −3.96 R. Within the ranked
set, scheduler rank carries no outcome signal (rank-1 −0.121 vs rank-4-10
−0.098), and the model's own `expected_net_r` is **anti-predictive**: the
highest-expectation quartile (mean expected +1.14) realizes the worst mean net
(−0.228) while Q2 is the only near-flat quartile (+0.014). Same inversion
direction as January (Q4 best there but still negative at −0.153; ordering
noisy both months — the expectation surface carries no usable signal).
Detail: `RESIDUAL_CHOICE_SET.json`, `CLARIFIERS.json`.

## 4. Cost band cost_r > 1.0 — airtight upstream, zero leakage

2,897 scoreable rows (11.95%) carry cost_r > 1.0; they sum −6,015.2 R = 38.77%
of pool loss (Jan: 4,908 rows, 54.17%). Every one is caught at S1 —
2,863 by `ev_negative_after_cost`, 33 by cost-packet refusal, 1 source-hold.
Physical: all 31,732 cost>1 physical rows are S1-caught. **Leakage into the
choice set: 0 rows in both months.** None of the 58 executed trades carries
cost_r > 1.0 (max executed cost_r 0.14137; January max 0.17655). Cost concentration is materially
lower than January (SPX500 mean cost 1.67 vs 2.39; NAS100 1.69 vs 2.25) —
consistent with true-UTC re-clocking pulling decisions off the worst spread
hours — yet the pool is still −0.64 R/row. Cost is not the whole February
story: mean gross is −0.151 before any cost.

## 5. Non-scoreable census (104,926 rows)

All 104,926 are `path_auditable_r_unscoreable` with null net proxy (no third
status; nothing unreadable). Blocker mix: cost_authority 92,361 (88.0%),
source_or_signature_authority 3,520, execution_fillability 3,499, other 2,937,
package_authority 2,316, remainder < 500 each. 2,610 non-scoreable rows were
scheduler-materialized. Detail: `NONSCOREABLE_CENSUS.json`.

## 6. Declined winners (7,498 scoreable rows with positive net proxy)

84.3% of winners (6,319) were refused at S1 — 4,871 by the cost-packet gate,
668 by ev-after-cost; S3 took 870, S2 304, S4 5. The winner pool sums +6,359.9 R
against −21,873.4 R of refused losers on the same gates: precision 30.9% vs
60.6% breakeven — no gate refusing winners was wrong to do so on average.

**NY-session LONG metals (CP's January factory survivor class): NOT positive in
February.** n=335 (session_bucket==ny, XAUUSD/XAGUSD, LONG): mean net −0.226,
mean gross −0.121, positive share 47.8%, sum −75.6 R. January same class:
+0.057 mean net, 66.1% positive, +22.0 R. The class flipped **gross**-negative
— it is not cost-killed (mean cost 0.105), the signal itself failed out of
window. Refusing gates on it also shifted: Jan was led by S2 signed-authority
(86) and S3 displacement-quality (80); Feb by S3 displacement-quality (74) and
S1 cost-packet (66). This independently corroborates the wave-18 first-read
REJECT from inside the funnel. (authority_session==ny variant: n=353, −0.221,
48.2% — same verdict.)

`liquidity_sweep_reclaim` × LONG is stable and bad in both months: Feb n=1,991,
−0.508 mean net (gross −0.077, cost 0.431); Jan −0.496. A cost-dominated class
whose gross is ~zero; the funnel prices it correctly. Detail:
`DECLINED_WINNERS.json`.

One residual pocket exists both months: selector-reject rows nonetheless
materialized for replay (Feb n=91: mean +0.131, 59.3% positive; Jan n=207:
−0.159, 52.2%) — n too small and sign-unstable to mean anything.

## 7. January comparison — same funnel, two plumbing drifts, one real shift

Stable: stage kill shares within 2.3 pp; framework mix within 1.6 pp
(fvg_fill 58.6%→57.7%, ob_retest 21.5%→22.8%); direction mix ~52/48 both;
scoreable share 18.0%→18.8%; zero cost>1 leakage both; S4 nearly inert both.

Shifted (real): selector reason mix moved from ev-negative-after-cost
(34.6%→29.0%) toward cost-packet-refused (49.0%→60.4%), +11.4 pp — but 4.55 pp
of that is the plumbing drift below. Choice set −41%. Pool severity improved
(−0.881→−0.640 mean net; cost 0.663→0.489) while gross improved only
−0.218→−0.151: February is cheaper, not better.

**Plumbing drift 1 (anomaly): the `cost_missing` class.** February has 5,876
rows (4.55%) with miss_reason `..._cost_missing` — a reason that does not exist
in January — confined to exactly three symbols: UKOIL_cash (2,532), USOIL_cash
(1,988), GER40 (1,356). Every scoreable row of those three symbols in February
(3,555 rows) carries a **constant defaulted cost_r = 0.12** (1 distinct value),
while GER40's own spread_r field has 1,554 distinct real values that the cost
ignores. January priced the same symbols with varying costs (GER40 mean 0.323,
411–1,342 distinct values). February's cost series for these three symbols is a
placeholder, and for GER40 it understates true cost — which makes those rows'
net proxies optimistic, i.e. the February REJECT is conservative with respect
to this defect.

**Plumbing drift 2 (anomaly): schema.** `pretrade_cost_packet_status` exists on
every January full-ledger row (REFUSED 128,293 / PASSED 25,132) and on **zero**
of 129,165 February rows — the CP_V1 emitter dropped the field the CJ_V7
emitter carried. Any tool joining on that key silently loses February.

Minor: January's finalizer classes `adaptive_replay_memory_guard_blocked`
(124 rows) and several preflight blocks are absent or near-absent in February;
February adds none except the cost_missing family. Full drift tables:
`JANUARY_COMPARISON.json`.

## Verdict

The February funnel behaved structurally like January's and every gate was
economically correct on the rows it refused; the pool's negativity is in the
gross signal (−0.151 R/row before cost), not in gate misbehavior. The one class
that looked positive in January (NY LONG metals) is gross-negative in February.
Two data-plumbing defects are real but both bias *toward* optimism, so they do
not rescue the window: defaulted flat 0.12 costs on UKOIL/USOIL/GER40, and a
dropped `pretrade_cost_packet_status` field.

## Files

- `FUNNEL_CENSUS.json`, `NONSCOREABLE_CENSUS.json` — full-ledger censuses (schema-mirrors of funnel_jan)
- `REFUSAL_OUTCOMES.json`, `CLARIFIERS.json` — pool-level gate economics (schema-mirrors of funnel_jan)
- `STAGE_WATERFALL.json`, `RESIDUAL_CHOICE_SET.json`, `COST_BAND_CROSS.json`, `DECLINED_WINNERS.json`, `JANUARY_COMPARISON.json`
- scripts: `extract_funnel_fields.py`, `census_full_ledger.py`, `funnel_tables.py`, `refusal_outcomes_and_clarifiers.py`
