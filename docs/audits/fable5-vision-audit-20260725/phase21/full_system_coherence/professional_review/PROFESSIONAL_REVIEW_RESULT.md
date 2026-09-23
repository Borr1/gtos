# Wave 21 process-attested outcome-blind professional setup review

Status: `FALSIFIER_AMENDED_BOUNDED_REVIEW_NOT_SYSTEM_CLOSEOUT`

Code/plan authority: `fe5ab2b15d2447d32473bfe8ec3d7b2f24caa346`

Review policy arm: retained `875037f1bc787009c6020be82c3883d9fcf85fa8`
0.20R policy on 2025-10-28, 2025-11-03, and 2025-11-07.

Judgment-freeze root:
`58605fef5f13dd5bf8d11c9af99db7761ee651fc78ba1cfb21fe0d1564437226`

## Findings first

1. The 20-row coverage sample is **process-attested outcome-blind**, not independently timestamp-proved.
   It was selected only from candidate-stage
   day, family, side, asset class, session, pretrade cost band, and raw Selector action. Target, stop,
   order, fill/no-fill, terminal disposition, realized cost, holding, and outcome were prohibited from
   sampling. The packet contains no expected value, downstream stage, or realized/terminal outcome.
   The recorded process froze professional judgments at `2026-08-09T05:23:41Z` before reading downstream
   rows, and the candidate-only builder reports zero downstream/outcome reads. However, freeze and unblind
   first entered Git together, so Git does not independently prove that chronology. The packet, judgments,
   and process receipt are hash-bound below.

   Freeze-audit correction: the review was outcome-blind but not perfectly probability-blind. Two current-
   FVG rows expose a causal predecision fill-probability estimate even though each row's
   `hidden_field_contract` says it was hidden. Those values were not sampling inputs; both rows were frozen
   `reject` under the recorded professional far-side-reference hypothesis. The original freeze is preserved
   rather than rewritten. Exact paths and values are in `PREDECISION_FREEZE_AUDIT.json`.

2. The professional blind dispositions were **12 reject, 6 wait, 2 reduce, 0 full trade**. This is a
   deliberately coverage-balanced inspection set, not a prevalence estimator. The raw Selector was more
   aggressive than the frozen professional judgment in 7 rows, more conservative in 1, and risk-inertly
   aligned in 12. After unblinding, every sampled row was a no-order miss: final system versus professional
   judgment was 12 aligned rejects, 6 risk-inert system rejects versus professional waits, and 2 system
   rejects versus professional reduces. These are frozen professional judgments and system comparisons, not
   proof that the proposed professional policy is superior. The sample does **not** validate order, fill,
   exit, cost, account, or economics quality.

3. The largest measured strategy-definition exposure is
   `predecision_close_far_side_of_unchosen_1p5R_reference`. Across the full retained
   population, 20,884 occurrences came from `current_fvg_fill`, `current_ob_retest`, or
   `current_breaker_re_entry`. At decision time, the latest closed M15 price was already beyond the
   generic 1.5R reference in **18,719 / 20,884 (89.6332%)**. Of those, raw Selector returned a
   risk-bearing action for **7,189** (`trade=1,647`, `reduce-risk=5,508`, `open-reduced-risk=34`), and the
   candidate trace carried **5,242** `new_position`/`replace_pending` Scheduler materialization intents.
   The arithmetic is exact; the earlier interpretation was not. The reference is `risk.min_rr` inheritance,
   explicitly labelled `UNCHOSEN`, not a source-owned thesis target. A resting LIMIT can remain physically
   valid after price moves to the far side and later retraces. Without a family expiry/re-arm contract, this
   measurement does **not** prove completed thesis, objective invalidity, or a source/Selector defect.

4. All **18,719** far-side-reference occurrences ended with effective action `reject`, order status
   `not_sent_missed_opportunity`, and **0 orders**, but the miss reasons are heterogeneous unrelated gates.
   Current code has no far-side-specific refusal by default, no expiry/re-arm contract, and no downstream
   cancellation guard for this condition. Zero orders is therefore descriptive correlation, not causal
   containment. It proves neither 18,719 bad trades nor that a later guard caught them.

5. Target and horizon authority is generic rather than independently family-owned. Every one of the **23,309**
   candidate occurrences has `risk_reward_ratio=2.0` and `dynamic_geometry_applied=true`, across all ten
   emitting families. In current source, every declared family target is explicitly `UNCHOSEN`; with the
   family policy off, candidates inherit `risk.min_rr`. The dynamic momentum policy defaults to 2.0R and
   the thesis horizon defaults to 32 M15 bars. A displacement, current POI, sweep, structural extreme,
   opening-range break, regime transition, lead-lag, and compression expansion therefore do not yet carry
   independently justified destination/horizon authority in this estate. This is an authority/exposure
   finding, not a conclusion that generic geometry should automatically cancel a candidate.

6. Two narrower **strategy-definition exposures** are source-code-wide; their proposed changes are
   B-policy hypotheses, not objective defects:

   - `structural_distance_extreme`: all **392** occurrences are emitted solely from a 50-bar position
     threshold (`>=0.97` short, `<=0.03` long) with no rejection/reversal confirmation. Both blind sample
     witnesses were professionally rejected under a reversal-confirmation preference. The missing mechanic is
     proved across 392 emissions; requiring confirmation is a policy hypothesis, not established superiority.
   - `session_open_range_break`: all **146** occurrences use exactly the first two session bars as the
     opening range and have no two-sided-sweep ambiguity guard. One blind witness swept both range extremes
     before closing below and was professionally rejected; the other was judged `wait` under a preference for
     a richer opening-range definition. The full-population count is the 146 emissions exposed to the current
     definition, not proof that it is wrong or that all 146 contain an actual two-sided sweep.

7. A separate outcome-aware diagnostic censused all 34 available ordered occurrences across deliberately
   mixed arms: 30 modelled fills and 4 no-fills; 17 stop, 7 target, and 6 filled time-stop terminals.
   All 34 join to account projection by `simulated_order_id`, but all 34 report close-side all-in cost
   `not_joined_in_replay_net_proxy_r`. The cohort proves an offline engineering path through order, modelled
   M1 fill/exit, and account projection. It does not provide broker-fill truth, complete post-lifecycle cost,
   setup-quality validation, or pooled economics.

8. The outcome-aware missed-candidate census is exhaustive rather than top-N: **540** missed occurrences
   have the counterfactual terminal label `target_reached_before_stop`. They are counterfactual paths, not
   realized trades and not evidence that the professional decision should have been `trade`.

## Authority and method

The controlling plan was created at `01446b38390f4e3d1f15dc26da3848a7b3718e6b` from baseline
`c994eb564c3cb97f1498ea7449dcd620192a91dd` and tightened at the current authority
`fe5ab2b15d2447d32473bfe8ec3d7b2f24caa346`. The current wording expressly forbids blind selection by
target, stop, time-stop, realized holding, final cost, or outcome and permits a later outcome-aware
diagnostic only if it is not used to validate setup quality.

The retained candidate population is 23,309 occurrences: 8,670 on Oct 28, 8,284 on Nov 3, and 6,355 on
Nov 7. Four candidate IDs that had already been exposed in earlier work were excluded from sample
eligibility only; they remain in all full-population counts. The eligible population was 23,305. The
owner-approved deterministic greedy maximum-marginal-coverage selection was frozen by exact occurrence
key with tie rule `sha256(seed|occurrence_key)`. It selected 20 rows and gave at least two witnesses for
every observed level of all seven allowed axes:

- 10/10 emitting families, exactly 2 each;
- both sides; 6/6 asset classes; 4/4 sessions; 5/5 cost bands; 5/5 raw Selector actions;
- 9 Oct 28, 5 Nov 3, and 6 Nov 7 rows.

Every sampled identity was independently regenerated from the raw source by the production market-state
orchestrator/generator before review. The packet includes causal closed-bar context only: D1 30 bars, H4
80, H1 168, M15 672; no M1/tick outcome path was attached. The exact source bindings and maximum source
timestamps are retained per row.

### Retained baseline bindings

| Day | Retained stage ledger | SHA-256 | Run-receipt SHA-256 |
|---|---|---|---|
| 2025-10-28 | `/private/tmp/wave21-minimal-repair-20251028-875037f1b-r4/harness_wave21_minimal_repair_20251028_875037f1b_r4_stage_ledger.jsonl.gz` | `89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991` | `3c3d138d1b6d73961206e8bbfed2138d076d546cbad85536aa29d86eac3bc06c` |
| 2025-11-03 | `/private/tmp/wave21-minimal-repair-20251103-875037f1b-r1/harness_wave21_minimal_repair_20251103_875037f1b_r1_stage_ledger.jsonl.gz` | `db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8` | `b6a50510a779f5871eb374d6d9ec01b9994348b56df7c520e880b6d4d2915323` |
| 2025-11-07 | `/private/tmp/wave21-minimal-repair-20251107-875037f1b-r1/harness_wave21_minimal_repair_20251107_875037f1b_r1_stage_ledger.jsonl.gz` | `e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835` | `00f45e4dca469fcb39ee6cb3dbca266bdb33cce81b0abcc96e8af594820b6c1c` |

Raw source manifests are
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests/october_2025.json`
at `72b967b4cbd5c7624337b5f3479784907bf04092624fe52daad5c1dd0c816af2` and
`.../manifests/november_2025.json` at
`2941ed91eb069e09d43e17d9c1773ca21a779f2efefc050707289ee96c1355b4`.

### Freeze bindings

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `PREDECISION_SAMPLE_MANIFEST.json` | 20 selected | `c4476845d942177558d0f890f2566a4f4d978217532fb7442f38bdee7987320b` |
| `PREDECISION_REVIEW_PACKET.jsonl` | 20 | `5602bf0f96ba66a968b7e178c638fda30bc87250a345b4c40bbd674860517dc7` |
| `PREDECISION_POPULATION_COUNTS.json` | 23,309 population | `8fb27149beaf454473997f64a1a5afd6952d5f41270d6ddd8caf3dba5379f81f` |
| `PREDECISION_JUDGMENTS_FROZEN.jsonl` | 20 | `6d66995c479d9d68ed987b5b5b2c835f134cbdb0c073769e46ecd3719b6ace31` |
| `UNBLINDED_SAMPLE_COMPARISON.jsonl` | 20 | `5364f196c4942b7af3902d984a32710a4826bc2001758a64240a4d76b2c0f57b` |

`PREDECISION_FREEZE_AUDIT.json` at
`91672133aeccb99c95ccb2bbbba592bb5c775c3ac3615a7405516225db054e67` records one metadata defect without
altering the historical freeze: two rows contain a duplicated causal predecision fill estimate.
`POST_FALSIFICATION_SEMANTIC_CORRECTION.json` at
`400ca2d62f9a41a52fb1a2d1f30e876cff6c8889c19823b69d51a671984fdd27` supersedes causal labels in the
immutable freeze-bound bytes. The valid claim is process-attested outcome-blind, not independently
timestamp-proved and not probability-blind.

## All 20 sampled rows

`Final` is the post-unblind final-system relation to the frozen professional disposition. `Terminal` is
shown only after the freeze and was not used for sampling or judgment. Full predicate, geometry, stop,
target/horizon, entry-reference/timing, context, repair-owner, and rationale fields are in
`PREDECISION_JUDGMENTS_FROZEN.jsonl`. Its `source_owned_target`, `completed thesis`, objective-defect, and
repair language is preserved as historical blind-review wording but superseded by
`POST_FALSIFICATION_SEMANTIC_CORRECTION.json`; those judgments are policy hypotheses.

| Review ID | UTC | Candidate | Session / cost band | Raw Selector | Frozen professional | First predicate failure/caution | Final | Terminal after unblind |
|---|---|---|---|---|---|---|---|---|
| W21-PRE-13B4C92791 | 10-28 00:45 | AUDUSD / displacement_continuation / LONG | tokyo / 0.10-0.20R | trade | reduce | predicate satisfied; generic target and mixed HTF | no order, system more conservative | stop before target |
| W21-PRE-D2A4030E4F | 10-28 03:00 | USDJPY / current_breaker_re_entry / SHORT | tokyo / 0.10-0.20R | trade | wait | predicate satisfied; wait for valid retest/re-entry | no order, risk-inert alignment | not filled |
| W21-PRE-E0F0C16667 | 10-28 03:45 | GBPJPY / current_breaker_re_entry / SHORT | off-session / 0.20-0.35R | reject | reject | close far side of unchosen 1.5R reference; expiry hypothesis | aligned reject | not filled |
| W21-PRE-1C00A40FE9 | 10-28 09:00 | EURGBP / liquidity_sweep_reclaim / SHORT | london / <=0.10R | source-required | reduce | predicate satisfied; source hold blocks expression | no order, system more conservative | time-stop mark |
| W21-PRE-4B4A3B5D9B | 10-28 09:15 | GER40 / current_fvg_fill / SHORT | london / 0.10-0.20R | reduce-risk | reject | close far side of unchosen 1.5R reference; expiry hypothesis | aligned reject | not filled |
| W21-PRE-C29E90AA04 | 10-28 10:00 | US30_cash / regime_transition_break / LONG | london / <=0.10R | reduce-risk | wait | predicate satisfied; family horizon not owned | no order, risk-inert alignment | time-stop mark |
| W21-PRE-03AE32FAC4 | 10-28 13:45 | UK100 / session_open_range_break / SHORT | ny / <=0.10R | reject | reject | two-sided trigger sweep; ambiguity-policy hypothesis | aligned reject | stop before target |
| W21-PRE-D795644BAF | 10-28 14:45 | GBPJPY / liquidity_sweep_reclaim / LONG | ny / 0.35-0.45R | reject | reject | predicate passes but cost/context reject | aligned reject | target before stop |
| W21-PRE-415C42A935 | 10-28 15:00 | UKOIL_cash / session_open_range_break / SHORT | ny / 0.20-0.35R | reject | wait | two-bar range; richer-definition policy hypothesis | no order, risk-inert alignment | time-stop mark |
| W21-PRE-8D6684462C | 11-03 01:15 | GBPJPY / current_ob_retest / SHORT | tokyo / 0.20-0.35R | reject | reject | close far side of unchosen 1.5R reference; expiry hypothesis | aligned reject | not filled |
| W21-PRE-673852DC49 | 11-03 03:45 | SPX500 / current_fvg_fill / SHORT | off-session / 0.10-0.20R | reduce-risk | reject | close far side of unchosen 1.5R reference; expiry hypothesis | aligned reject | not filled |
| W21-PRE-610FA55FC3 | 11-03 08:45 | EURJPY / displacement_continuation / SHORT | london / 0.10-0.20R | source-required | wait | predicate satisfied; wait for coherent authority/context | no order, risk-inert alignment | time-stop mark |
| W21-PRE-D7DBF4C11B | 11-03 15:30 | ETHUSD / regime_transition_break / SHORT | off-session / <=0.10R | open-reduced-risk | wait | predicate satisfied; family horizon not owned | no order, risk-inert alignment | time-stop mark |
| W21-PRE-7A0A64E816 | 11-03 23:45 | JP225 / volatility_compression_expansion / SHORT | off-session / <=0.10R | reject | reject | mechanical predicate only; context/expansion weak | aligned reject | time-stop mark |
| W21-PRE-B12EFC3B55 | 11-07 01:45 | XAUUSD / volatility_compression_expansion / LONG | off-session / <=0.10R | open-reduced-risk | wait | breakout clearance only about 0.06 ATR | no order, risk-inert alignment | time-stop mark |
| W21-PRE-FD0FF3FAAF | 11-07 03:00 | UKOIL_cash / cross_asset_lead_lag / LONG | off-session / 0.35-0.45R | reject | reject | predicate passes; cost/noise/context reject | aligned reject | ordered-tick sequence required |
| W21-PRE-1A74067A40 | 11-07 05:15 | XAGUSD / structural_distance_extreme / SHORT | off-session / >0.45R | reject | reject | bare extreme; confirmation-policy hypothesis | aligned reject | target before stop |
| W21-PRE-390E2C874D | 11-07 15:15 | CHFJPY / current_ob_retest / LONG | ny / 0.20-0.35R | reject | reject | close far side of unchosen 1.5R reference; expiry hypothesis | aligned reject | not filled |
| W21-PRE-0A069D1CBE | 11-07 20:00 | NZDUSD / cross_asset_lead_lag / LONG | off-session / >0.45R | reject | reject | predicate passes; cost/noise/context reject | aligned reject | target before stop |
| W21-PRE-2F0431968F | 11-07 20:45 | BTCUSD / structural_distance_extreme / SHORT | off-session / 0.35-0.45R | reject | reject | bare extreme; confirmation-policy hypothesis | aligned reject | target before stop |

## Full-population strategy-definition exposure census

| Family | Occurrences | Measured exposure; policy conclusion not proved |
|---|---:|---|
| current_fvg_fill | 13,321 | generic 2R/32-bar authority; 11,815 closes far side of unchosen 1.5R reference |
| current_ob_retest | 6,394 | generic 2R/32-bar authority; 5,955 closes far side of unchosen 1.5R reference |
| current_breaker_re_entry | 1,169 | generic 2R/32-bar authority; 949 closes far side of unchosen 1.5R reference |
| liquidity_sweep_reclaim | 765 | generic 2R/32-bar target/horizon authority |
| displacement_continuation | 653 | generic 2R/32-bar target/horizon authority |
| structural_distance_extreme | 392 | generic target/horizon; all 392 use a bare extreme with no confirmation; adding one is a hypothesis |
| cross_asset_lead_lag | 349 | generic 2R/32-bar target/horizon authority |
| session_open_range_break | 146 | generic target/horizon; all 146 use a two-bar range/no two-sided-sweep exclusion; changing it is a hypothesis |
| volatility_compression_expansion | 74 | generic 2R/32-bar target/horizon authority |
| regime_transition_break | 46 | generic target/horizon; source declares H1/H4/D1 birth while implementation emits M15 |
| **Total** | **23,309** | **all 23,309 use the same 2R dynamic final geometry; the active contract's default thesis horizon is 32 M15 bars** |

The exact far-side-of-unchosen-reference counts by day are 7,013 Oct 28, 6,780 Nov 3, and 4,926 Nov 7.
`PREDECISION_POPULATION_COUNTS.json` preserves the earlier provisional `target_through`/`source_owned`
labels because it is freeze-bound; `POST_FALSIFICATION_SEMANTIC_CORRECTION.json` supersedes only their
meaning, not their arithmetic. Current downstream counts and every heterogeneous miss reason are in
`FAR_SIDE_UNCHOSEN_REFERENCE_DOWNSTREAM_CENSUS.json`.
Its file SHA-256 is `4a175b5c413b021a85273995ef1dbff2c51715c59e23251cb570e6880d499178`
and structured census root is `1fd0385822cab282b2c4a140c05c17433fd9be39fa0c1cf5098100db8ce11b59`.

Source evidence for the family-wide findings:

- `src/components/broader_origin_generators.py:886-921` emits structural extremes from the 50-bar
  position alone.
- `src/components/broader_origin_generators.py:927-996` defines the opening range as its first two bars,
  rejects only a prior close outside it, and has no two-sided-sweep guard.
- `src/components/broader_origin_generators.py:2514-2614` says every family target is `UNCHOSEN` and
  documents that the floor still binds all emissions; `:2659-2705` inherits `risk.min_rr` when the policy
  is off.
- `src/components/dynamic_target_stop_geometry_v4.py:97-106` gives momentum a default 2.0R destination;
  `:344-348` defaults the thesis horizon to 32 M15 bars.
- `src/components/broad_origin_emission_contract.py:54-76` makes far-side refusal optional and default
  `None`; `:234-296` labels the bin but admits it unless that optional policy is configured.

## Unblinded chain status

| Chain stage | What current disk proves | Status |
|---|---|---|
| raw source -> market state | All 20 sampled occurrences use bound causal closed bars and exact raw reconstruction; this review did not prove conservation of every expected source slot for all 23,309 | `PROVED_SAMPLE_ONLY`; full-slot route `NOT_EVALUABLE` here |
| market state -> candidate/family | Exact candidate identity reconstructed for 20/20; full population/family mechanics counted; professional expiry/confirmation preferences remain hypotheses | mechanics `PROVED`; policy superiority `NOT_EVALUABLE` |
| raw Selector | Candidate-stage actions captured before outcomes; 7 more aggressive, 1 more conservative, 12 risk-inert versus frozen professional judgment | `PROVED_SAMPLE_ONLY` |
| package/Scheduler | 20/20 sample rows end no-order; all 18,719 far-side-reference rows also end no-order for heterogeneous unrelated reasons; no far-side cancellation guard exists | counts `PROVED`; causal containment `NOT_PROVED` |
| risk/headroom | A risk probe is present for every sample occurrence, but none acquired final order authority. The 34 mixed-arm diagnostic contains modelled requested/approved risk | `NOT_EVALUABLE` for professional risk sizing; mixed-arm path `TEST_ONLY` |
| final order | No blind sample order. Separate mixed cohort has 34 simulated orders | blind sample `NOT_EVALUABLE`; diagnostic `TEST_ONLY` |
| fill/no-fill | No blind sample fill. Mixed cohort has 30 ordered-M1 modelled fills and 4 no-fills, explicitly not broker truth | blind sample `NOT_EVALUABLE`; diagnostic `TEST_ONLY` |
| exit/lifecycle | No blind sample trade. Mixed cohort has 17 stops, 7 targets, 6 time-stop marks | blind sample `NOT_EVALUABLE`; diagnostic `TEST_ONLY` |
| cost | Pretrade packet/cost band is bound for candidates. Realized component cost is null for the blind sample; all 34 mixed orders lack joined close-side all-in cost | pretrade `PROVED`; post-lifecycle `NOT_EVALUABLE` |
| account | No blind sample account event. All 34 mixed orders join to offline account projection by simulated order ID | blind sample `NOT_EVALUABLE`; diagnostic `TEST_ONLY` |

## Outcome-aware diagnostic, kept separate

The 34-order cohort intentionally uses three different treatments and must never be pooled for economics:

| Day | Arm/treatment | Authority | Orders / fills | Terminals | Promising rejects |
|---|---|---|---:|---|---:|
| 2025-10-28 | `8762e0480`, 0.45R treatment | rejected policy treatment | 12 / 10 | 5 stop, 3 target, 2 time-stop, 2 no-fill | 200 |
| 2025-11-03 | `f3ae1a210`, retained 0.20R plus XAU Scheduler repair | downstream diagnostic only | 11 / 9 | 5 stop, 2 target, 2 time-stop, 2 no-fill | 157 |
| 2025-11-07 | `8762e0480`, 0.45R treatment | rejected policy treatment | 11 / 11 | 7 stop, 2 target, 2 time-stop | 183 |

The ordered family census is `current_fvg_fill=12`, `current_ob_retest=4`,
`displacement_continuation=9`, `liquidity_sweep_reclaim=8`, and `session_open_range_break=1`. All 16
ordered current-family candidates had a predecision close not far side of the unchosen 1.5R reference;
this is descriptive and does not validate an expiry rule. The complete 540 promising-reject census is:
liquidity sweep 143, current FVG 135, displacement
87, structural extreme 62, lead-lag 58, current OB 28, opening-range 15, breaker 10, regime transition 2.

Bindings and claim boundaries are in `OUTCOME_DIAGNOSTIC_CENSUS_SUMMARY.json`, root
`92c66990823d9c738f46d58f954b74cb6dccbfa264ee0341f796f5a3ecfacb4f`. Ordered rows are in
`OUTCOME_DIAGNOSTIC_ORDERED_34.jsonl` at
`62ebc2001857a0b85c4fb1421596270c9a5a1fdf41f0de982f1f951e6212074c`; exhaustive promising rejects are
in `OUTCOME_DIAGNOSTIC_PROMISING_REJECTS_540.jsonl` at
`867137abc3e39ccebf4e5b3f493851630f277eb12d4d9e85f547a5d459c17da7`.

## Current-artifact and stale-claim map

| Item | Treatment now |
|---|---|
| `WAVE21_FULL_SYSTEM_COHERENCE_PLAN.md` at `fe5ab2b15` | current controlling plan; supersedes its looser `01446b383` wording |
| `POST_FALSIFICATION_SEMANTIC_CORRECTION.json` | current interpretation authority for this review; preserves original freeze bytes and supersedes their causal labels |
| `875037f1b` ledgers for all three blind-review days | sole retained policy arm for this setup-quality sample |
| Nov 3 `f3ae1a210` | downstream/XAU Scheduler-repair diagnostic only; excluded from blind sample authority even where predecision bytes match |
| Oct 28 and Nov 7 `8762e0480` | rejected 0.45R treatment, diagnostic only |
| `OUTCOME_DIAGNOSTIC_*` | explicitly outcome-aware and mixed-policy; cannot validate setup quality or pooled economics |
| held lane/P1 raw sources and manifests | source authority for reconstruction, hash-bound above |
| `/private/tmp/wave21-minimal-repair-*` ledgers | current bytes verified and hash-bound, but path durability is weak because `/private/tmp` is ephemeral; do not cite them without the hashes/receipts |
| old Claude/Opus session prose, earlier top-N examples, and pre-tightening blind-set claims | context only; no verdict in this report depends on them |
| packet claim `predicted_fill_probability_hidden=true` | stale/incorrect for 2 rows; corrected by `PREDECISION_FREEZE_AUDIT.json` without rewriting the freeze |
| freeze-bound `target_through`, `source_owned_target`, completed-thesis, defect, repair, or guard wording | historical/provisional judgment language, superseded by `POST_FALSIFICATION_SEMANTIC_CORRECTION.json`; arithmetic retained |
| broad `research_timewarp` outputs | offline engineering comparator only; not W7-native/live or broker authority |

## Prioritized critical path

1. Preregister a **per-family expiry/re-arm/confirmation comparator** on genuinely untouched evidence. It
   must separately test current-POI far-side-reference handling, structural-extreme confirmation, and
   opening-range/two-sided-sweep definitions; this review does not authorize any one of those policies.
2. Keep the 23,309 denominator and compare complete portfolio effects without threshold search or optimizing
   against these 20 reviewed rows. Freeze the next judgment/evidence boundary in an independently committed
   or externally timestamped artifact before unblinding.
3. Independently of that policy comparator, close evidence gaps in source-slot/occurrence conservation,
   ordered tick or exact no-fill authority, ticket-bound exit lifecycle, post-lifecycle component cost, and
   account reconciliation. Broker-real fill and live/W7 transfer remain `NOT_EVALUABLE`.

No trading policy, threshold, config, live/VPS surface, broker state, or activation state was changed by this
review. No heavy replay was run.
