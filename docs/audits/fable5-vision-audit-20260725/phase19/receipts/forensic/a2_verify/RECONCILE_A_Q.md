# A2 RECONCILE — FA Phase-1 contradiction register A–Q, resolved from raw data

Lane: RECONCILE (Session FA-continuation Phase A2). Date: 2026-08-03.
Register source: `phase19/FA_CONTINUATION_VERIFIED_STATE.md` §4 (only §4 read, per mandate).
All recomputation from RAW inputs: the two compact pools (streamed line-by-line), the two raw
TRADE/ORDER ledgers, the full January MISSED ledger (153,425 rows, 1.34 GB, streamed), the CQ
sidecar (streamed), and the two lane trade tables. Sol/FA receipts were used only as CLAIMS.
**February reads are attribution-only under owner_mandate_20260801.** March and live-forward
(2026-07-29+) outcomes untouched. No arms, replays, or test suites run; no source file edited.

Computation receipts in this directory: `POOLS_PASS_RESULT.json`, `TRADES_ORDERS_RESULT.json`,
`MISSED_LEDGER_RESULT.json`; scripts `reconcile_pools_pass.py`, `reconcile_trades_orders.py`,
`reconcile_missed_ledger_pass.py`, `reconcile_followups.py`. Claim-by-claim table:
`RECONCILE_VERIFY.md` / `.json`.

Status summary: **15 rows RESOLVED (A–P except Q), 1 STANDS as meta (Q).** Two register
sub-claims are REFUTED in the process (C's prose-mismatch parenthetical; N's 26,427), one
register label corrected (E's "all-scoreable set"), one claim refined (J's Feb gap), and one
count corrected (O's "does not exist").

---

## A. Two incompatible loss-class rules — RESOLVED (recommendation below; orchestrator ratifies)

Both rules re-implemented from their receipt definitions and applied to both months' **raw
TRADE ledgers** (not to FA's tables). Every cell of every published table reproduces exactly,
and both rules sum to each month's executed net exactly:
Jan −5.50620829 R (55 scoreable; 2 unscoreable at 0), Feb −3.96139869 R (58 scoreable).

**January (57 trades) under both rules** [recomputed]:

| class | Jan rule (MFE≥0.5⇒exit) | Feb rule (mfe<0.25⇒dir; mfe−cost>0⇒exit) |
|---|---|---|
| winners (target / other) | 6 / +11.9111 and 17 / +12.2308 | 6 / +11.9111 and 17 / +12.2308 |
| direction_wrong | **17 / −18.3247** | **11 / −9.6973** |
| exit_geometry | **11 / −9.9410** | **21 / −19.9509** |
| horizon_marked | 4 / −1.3825 | 0 |
| cost_dominated | 0 | 0 |
| unscoreable | 2 / 0 | 2 / 0 |

**February (58 trades) under both rules** [recomputed; the Jan-rule column was never published
anywhere — computed fresh here]:

| class | Jan rule | Feb rule |
|---|---|---|
| winners (target / other) | 2 / +3.8567 and 22 / +15.7581 | 2 / +3.8567 and 22 / +15.7581 |
| direction_wrong | **16 / −15.3552** | **10 / −9.5935** |
| exit_geometry | **9 / −6.8798** | **23 / −13.9654** |
| horizon_marked | 5 / −1.1630 | 0 |
| cost_dominated | 4 / −0.1782 | 1 / −0.0173 |

The rule choice swings the exit-vs-direction split ~2× in BOTH months (Jan 17/11 ↔ 11/21;
Feb 16/9 ↔ 10/23) — the register's "never quote them side by side" is confirmed as necessary.

**Recommendation — adopt the Feb rule (the counterfactual-exit rule) as canonical.**
The classes exist to route repair: `exit_geometry` must collect exactly the losses an
exit-policy change could in principle have recovered, and `direction_wrong` the losses no exit
policy could touch. The Feb rule operationalizes both causally, per trade, against the trade's
own path and own cost: `direction_wrong` ⇔ the ordered path never offered ≥0.25 R of favorable
excursion (no exit could have won), and `exit_geometry` ⇔ `mfe − cost > 0` (a net-profitable
exit existed and the machinery failed to take it). The Jan rule's fixed MFE≥0.5R cut answers
neither question: it files 9 January trades carrying −9.72 R and 7 February trades carrying
−5.84 R under "direction" even though each had a bankable net-profitable exit on its own path —
precisely the repairable losses the class exists to isolate — and its mechanism-named remainder
(`horizon_marked`) states how a trade closed, not why it lost money. Under the Feb rule,
`stop_hit`/`horizon_marked` land empty in both months because every loser is exhausted into the
two causal buckets — the property a loss-attribution partition should have. Two knobs to
disclose whenever it is quoted: the 0.25 R noise floor is a declared threshold (not derived),
and the counterfactual exit is charged the full trade cost (conservative — an early exit pays
less swap). The full Jan-rule→Feb-rule movement cross-tab (per month, with net sums) is in
`TRADES_ORDERS_RESULT.json → movement_jan_rule_to_feb_rule`; use it as the citation bridge for
previously published Jan-rule numbers.

**Canonical restatement (Feb rule = the rule of record, pending orchestrator ratification):**

| class | January (57) | February (58) |
|---|---|---|
| target_hit | 6 / +11.9111 | 2 / +3.8567 |
| other (winner_non_target_exit) | 17 / +12.2308 | 22 / +15.7581 |
| cost_dominated | 0 | 1 / −0.0173 |
| direction_wrong | 11 / −9.6973 | 10 / −9.5935 |
| exit_geometry | 21 / −19.9509 | 23 / −13.9654 |
| unscoreable | 2 / 0.0000 | 0 |
| **sum** | **−5.50620829** | **−3.96139869** |

The two stable-signature observations survive restatement: direction_wrong is nearly constant
across months (−9.70 vs −9.59 R), and exit_geometry is the largest loss class in both.

## B. Jan executed breaker count 9 vs 8 (same +4.356 R) — RESOLVED

From the raw Jan TRADE ledger: **9 rows** with `origin_family == 'current_breaker_re_entry'`
(9 distinct candidate_ids; substring match over origin/framework/setup catches the same 9);
**8 are scoreable**; the 9th — `broadorigin_93c40ba45797157d…` USOIL_cash — is one of the two
`terminal_r_unscoreable` trades (net_r None). Net over the scoreable 8: **+4.35575072 R**.
Origin of the discrepancy: TRADES_JAN counted ledger ROWS (9; the null-net row adds 0 to its
sum), while TRADES_FEB's January reference used its `group_stats`, which SKIPS null-net rows
(8). Same set, same sum, two denominators. **Canonical: 9 executed / 8 scoreable / +4.3558 R
over the scoreable 8; quote "n=9 (8 scoreable)".**

## C. NY-metals variant labels — RESOLVED (and the register's mismatch sub-claim REFUTED)

Recomputed from the Jan pool over metals-LONG (XAUUSD/XAGUSD × LONG, 1,467 rows):

| definition | n | sum net R | pos share |
|---|---|---|---|
| `authority_session == 'ny'` | **411** | **+12.7494** | 65.2 % |
| `route_session == 'ny'` | 411 | +12.7494 | (identical set: XOR = 0 rows) |
| `route_session=='ny' OR session_bucket=='ny'` (the DECLINED_WINNERS prose) | 411 | +12.7494 | (OR degenerates) |
| `session_bucket == 'ny'` | **386** | **+21.9856** | 66.1 % |

**n=411 / +12.75 belongs to `authority_session` (≡ `route_session` — the two select the
identical row set here); n=386 / +21.99 belongs to `session_bucket`.** `session_bucket=='ny'`
is a strict subset of `route_session=='ny'` (0 rows outside; the 25 excess rows are
route/authority-ny with a different bucket, and they carry −9.24 R net, which is the whole
+21.99 → +12.75 difference). Consequence: the register's parenthetical *"the prose label in
DECLINED_WINNERS.json does not match the number it reports"* is **REFUTED** — the prose
definition `(route_session=='ny' OR session_bucket=='ny')` evaluates to exactly the n=411 /
+12.7494 it reports, because the OR's second arm adds nothing. Any future quote must name the
session field; the two variants differ by 25 rows and 9.24 R.

## D. Three "January residual choice set" figures — RESOLVED (reconciled, all three verified)

| def | population | physical | scoreable | mean net R |
|---|---|---|---|---|
| A | `broker_pretrade_cost_executable AND selector_action ∈ {trade, open-reduced-risk, reduce-risk}` | n/a (pool-only def) | **4,509** | **−0.198588** |
| B | `scheduler_materialization_status == 'scheduler_option_materialized'` | 8,581 | **4,095** | **−0.212678** |
| C | `effective_selector_action ∈ {trade, reduce-risk, open-reduced-risk} AND materialized` | **7,575** | **3,242** | **−0.204807** |

Overlaps (scoreable): A∩B 3,888; A\B 621 (mean −0.0923, 58.5 % positive); B\A 207 (the
softened router-rejects). Exact membership reconciliation: **C = 3,038 rows from A∩B + 204
rows from B\A; B = C + 853 materialized rows whose EFFECTIVE action is `reject`** (850 of them
with a risk-bearing SELECTOR action — the unpublished mirror of row I's softening: selector
risk-bearing → effective reject → still materialized). Within materialized, effective actions
are {open-reduced-risk 3,023, reject 853, reduce-risk 199, trade 20}. The three figures are
three different, individually correct populations: A = the pre-materialization clean menu,
B = everything the scheduler literally ranked, C = ranked AND still effectively risk-bearing.
**Cite C (7,575 / 3,242 / −0.205) when "what the scheduler chose from" is meant with effective
authority; cite B for "literally ranked"; never average them.**

## E. Picked-vs-menu baselines −0.213 vs −0.722 — RESOLVED (both verified; register label corrected)

- **−0.213** = mean `opportunity_net_proxy_r` of Def-B (scheduler-ranked declined set,
  n=4,095): recomputed **−0.212678**. VERIFIED.
- **−0.722** = mean over the **55 matched executed trades** of the mean outcome of each trade's
  own choice set (all pool rows sharing the trade's exact `decision_time_utc`, excluding the
  chosen candidate_id): recomputed **−0.72247086** (Feb analog −0.66506073). VERIFIED — but the
  register's own label for it, "all-scoreable set", is wrong: the all-scoreable pool mean is
  **−0.880657**. −0.722 is a trade-timestamp-weighted quantity from SCORECARD's
  `chosen_percentile`, not a pool-wide mean.
- **The one-line caveat:** *"−0.213 is the mean of the scheduler-RANKED declined set (n=4,095);
  −0.722 is the mean outcome of the 55 executed trades' own same-timestamp choice sets (and
  −0.881 is the whole scoreable pool); they answer three different questions — quoting any two
  as the same baseline manufactures a fake 3× discrepancy."*

## F. Pool key counts 78 / 101 / "80 fields" / 47 — RESOLVED

- Jan compact pool: **78 keys, uniform on all 27,658 rows** (0 drift variants). VERIFIED.
- Feb compact pool: **101 keys, uniform on all 24,239 rows**; a strict superset of Jan's 78
  (+23 path/outcome fields, e.g. `opportunity_gross_r`, `opportunity_close_reason`,
  `terminal_outcome`, first-touch times). VERIFIED.
- **"80 fields" (SCORECARD §7) is the full MISSED-ledger row width, not a pool width**: every
  one of the 153,425 January missed-ledger rows carries exactly **80 keys** [measured].
  The pool is a renamed projection of it (14 ledger keys dropped, 12 pool keys renamed in,
  e.g. `missed_package_replay_order_executable_final_blocker_class` → `final_blocker_class`).
  As a statement about the pools, "80" is REFUTED (78/101 are the pool numbers); the
  substantive half of the SCORECARD sentence — Feb pool contains every Jan pool field, no
  score fields missing — is TRUE.
- **47** = the cartographer enum scan's field subset (`JAN_POOL_ENUMS.json` scans 47 fields of
  the 78). VERIFIED as a subset count, not a schema width.

## G. `cq_sidecar.total_observations = 0` vs 3,229,819 — RESOLVED (crosscheck bug confirmed)

Streaming recount of the CQ sidecar: **27,658 rows; total path observations = 3,229,819**
(sum of `len(ordered_path_observations)`; per-row 3…120, M1 bars over the 120-min horizon).
The prose figure 3,229,819 is VERIFIED. The crosscheck's 0 is a bug in
`priors/verify_pool_crosschecks.py:129-132`: it sums keys named `observations` /
`n_observations`, neither of which exists — the field is `ordered_path_observations` (the
script's own `row_keys` output lists it, so the receipt refutes itself). Note the commission
brief's shorthand "3,229,819 rows" is observation-count, not line count: the file has 27,658
lines (one per scoreable candidate).

## H. Declined-winner partitions, totals 7,706 / +6,447.2 R — RESOLVED (cross-walk now exists)

Pool recount: **7,706 positive scoreable rows summing +6,447.2475 R** (losers 19,952 /
−30,804.4464). VERIFIED. The final-blocker partition of the 7,706 reproduces DECLINED_WINNERS
cell-for-cell (cost_authority 4,733, package_authority 1,075, other 1,049, scheduler_selection
303, execution_fillability 283, selector_materialization 138, fill_realism 62, daily_lockout
33, marketable_guard 30). The missing cross-walk is now built:
`POOLS_PASS_RESULT.json → january.H_crosswalk_blocker_x_selreason_positives` (final-blocker ×
selector-reason joint over the 7,706; top cell cost_authority × cost_packet_refused 3,985).

## I. Funnel non-monotonicity 3,536 + 3,281 — RESOLVED (both verified, delta identified)

Full-ledger recount (153,425 rows): `selector_action=='reject' AND materialized` = **3,536**,
all with reason `admission_quality_dynamic_router_refused_candidate_use`; effective action
open-reduced-risk on 3,526, still-reject on 10; scoreable split 207 / 3,329 (the pool-side 207
= 204 open-reduced + 3 reject, matching FUNNEL_JAN §1). Packet REFUSED = **128,293**; final
blocker cost_authority = **125,012**; delta = **3,281** — and the delta is now identified
row-level: **all 3,281 are non-scoreable REFUSED rows with final blocker
`source_or_signature_authority`** (non-scoreable REFUSED = 104,564 cost_authority + 3,281
source_or_signature_authority). Scoreable side: REFUSED 20,448 == blocker cost_authority
20,448, exactly as claimed.

## J. 61/66 selected probes vs 57/58 trades — RESOLVED (Jan verified; Feb refined)

Row-level from the raw ORDER ledgers, keyed (candidate_id, decision_time_utc):

- **January**: 122 order rows = 61 `pending_accepted` + 57 `filled` + 4 `expired_unfilled`.
  Accepted−filled keys == expired keys **exactly**; trade-ledger keys == filled keys. The 4-probe
  gap IS unfilled/expired, now verified row-level, not just "consistent with".
- **February**: 132 order rows = 66 `pending_accepted` + 58 `filled` + 7 `expired_unfilled`
  + **1 `cancelled_replaced_by_scheduler_v4`**. The 8-probe gap is **7 expired + 1
  scheduler cancel-replace** (`broadorigin_a8c9f3ae6b1a2058…` XAUUSD SHORT 2026-02-18T15:15Z;
  that candidate_id carries 9 accepted / 8 filled rows across the month, so the cancelled
  instance is a re-fire that was replaced, not a lost fill). The register's "consistent with
  unfilled/expired" was 7/8 right for February; the 8th probe is a cancel-replace, the only
  non-expiry probe loss in either month (January's `cancel_replace_event_count` is 0).

## K. `final_selection_claim` False on ALL rows — RESOLVED (verified everywhere it exists)

rg over the raw ledgers: false on **2,016/2,016** (Jan scorecard), **69,792/69,792** (Jan
decision), **1,920/1,920** (Feb scorecard), **62,328/62,328** (Feb decision); zero `true`
anywhere. The field does not exist in either compact pool (0 rows). The reading stands: it is
a provenance flag; find trades via `selected_probe_count` or the TRADE ledger.

## L. Feb binary_population 950/3,660 vs close-reason 2,811/11,499 — RESOLVED (both pinned)

- **Close-reason counts** (`opportunity_close_reason`, ≡ `terminal_outcome` on all 24,239
  rows): `target_reached_before_stop` **2,811**, `stop_reached_before_target` **11,499**
  (plus 6,435 `time_stop_close_mark_from_m1`, 742/693/635/539/538/278/69 others). VERIFIED.
- **`binary_population` 950/3,660** = rows whose net+cost reconstruction lands within **1e−9
  of the FIXED endpoints {+2.0, −1.0}**: recomputed 950/3,660 exactly (with each row's own
  `policy_target_r` it is 953/3,660 — 3 rows hit non-2.0 targets exactly). It is a
  float-exactness SUBSET, not an outcome population: on the Feb pool's native
  `opportunity_gross_r` every binary-close row sits exactly on its endpoint — **2,880 targets
  (= 2,811 `target_reached` + 69 `selected_policy_replay:final_target`) and 12,192 stops
  (= 11,499 + 693 `selected_policy_replay:stop_loss`)**.
- **The caveat that prevents the misquote:** *"hit_rate 0.206 = 950/4,610, a share within the
  float-exact endpoint subset of the gross reconstruction; precision 0.309 = 7,498/24,239
  net-positive share of the whole pool. Different numerators, different denominators, different
  measures — never adjacent without labels."*

## M. Endpoint tolerance counts — RESOLVED (every variant reproduced and attributed)

January, gross reconstructed as `opportunity_net_proxy_r + cost_r` (the compact pool has no
native gross field; neither does the full missed ledger — checked):

| variant | target | stop |
|---|---|---|
| FIXED 2.0 endpoint, tol 1e−9 (= the pool receipt's `binary_population` method) | **678** | **3,270** |
| per-row own `policy_target_r`, tol 1e−9 | 682 | 3,270 |
| per-row own target, tol 1e−6 (the register's "1e−6-near") | **3,072** | **15,057** |
| crosscheck heuristic (`source_bound_signal_r` vs target/−1) | 7 | 0 |

All four register numbers reproduce; the 678-vs-682 gap is exactly 4 rows whose non-2.0 target
was hit to 1e−9 (ids in `POOLS_PASS_RESULT.json`). The [7,0] in POOL_CROSSCHECK is not a bug
but a different field: `source_bound_signal_r` is the signal bound, not the outcome — it should
never be used for endpoint counting. Feb analogs: fixed 950 / own 953 / 1e−6 2,880; stops
3,660 (1e−9) / 12,192 (1e−6) — and 1e−6 on the reconstruction equals the native-gross exact
population, so tolerance-vs-basis fully explains every published pair.

## N. `policy_target_r` distinct counts — RESOLVED (distincts verified; one count corrected)

- Jan distinct values: **1,231** VERIFIED (= 1,230 one-off non-2.0 values + `2.0`).
  Feb distinct: **988** VERIFIED (= 987 + 1).
- **"2.0 on 26,427/27,658" is REFUTED: the count is 26,428**/27,658 (27,658 − 26,428 = 1,230
  non-2.0 rows; the register's 26,427 is internally inconsistent with its own 1,231 distinct —
  1,231 non-2.0 rows would make 1,232 distinct values). Feb: 2.0 on 23,252/24,239.
  Never assume uniform 2.0 — confirmed; the executed trades' 2.0-everywhere is a property of
  the 57-trade slice, not the pool.

## O. Commission cites `CJ_RECLOCKED_ARM_S0R0_V7_ECONOMICS.json` "which does not exist" — RESOLVED (corrected)

The file **EXISTS on disk** in the wave16 receipts directory: 186,372,381 bytes, born
2026-08-01 01:45, `git status` **untracked** (`??`) — a full-ledger economics dump that was
never committed. So the register row is wrong as a filesystem claim and right only as a
committed-tree claim. The two receipts the register names as real
(`CJ_RECLOCKED_ARM_S0R0_V7.json`, `CJ_CD_BASELINE_S0R0_ECONOMICS_V1.json`) both exist and are
committed. Rule going forward: cite the committed receipts; the untracked 186 MB dump is
machine-local state.

## P. Join hazards — RESOLVED (pinned with both quantifications)

Jan pool: 27,658 rows / **21,880 distinct candidate_ids** → **5,778 excess rows** (the "~5,778
mis-joins" figure = rows beyond the first per id); **6,745 rows** live in multi-instance ids
(the rows a bare-id join would make ambiguous). The full tuple **(candidate_id,
decision_time_utc, symbol, side) is unique: 0 duplicates** — VERIFIED as the join key.
Feb: 18,752 distinct ids, 5,487 excess rows, 6,299 rows in multi-id groups, 0 tuple duplicates.

## Q. "No Phase-1 output is internally truncated" — STANDS (meta; not data-resolvable)

A completeness assertion over all Phase-1 outputs cannot be recomputed from pools. Weak
corroboration: every Phase-1 number this lane tested (≈40 quantities across 7 receipts)
reconciled exactly against raw data except the three corrections listed above (N's off-by-one,
F's "80", O's existence) — none of which is a truncation. What would settle it: a
file-by-file structural walk of every Phase-1 JSON, out of this lane's scope.
