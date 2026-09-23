# w0_DATA_DICTIONARY — the shared map for the wave-19 discovery swarm

Generated 2026-08-06 by `w0_dictionary_build.py` from the pool itself, from
`src/` at this worktree's HEAD, and from the measurement receipts listed in §6.
**Every number here was measured, not quoted.** Where this file contradicts the swarm brief, the
contradiction is flagged inline with the measurement that settles it.

---

## 0. THE SIX THINGS TO READ FIRST

These change how you must interpret every query you are about to run.

**0.1 — The pool contains ZERO executed trades. It is 100% counterfactual, by construction.**
The raw ledger `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl` holds **153,425 rows**; the pool is the
**27,658 (18.03%)** that pass the scoreability gate at
`v4_timewarp_simulated_live_research_loop.py:28130-28140`. That gate requires `not headline_r_scoreable`,
so a candidate that actually reached headline execution is **excluded**. `missed_opportunity_r_scoreability_status`
is the constant `diagnostic_opportunity_r_scoreable` on all rows *because that is the filter*. Never describe this
pool as "what the system traded".

**0.2 — The binding cost gate is the SPREAD cap, not the 0.15 total.** The brief names
`total_cost_r_exceeds_limit` vs `0.15`. There are **two independent limbs** in
`broker_net_cost_engine.py:pretrade_cost_refusal_reasons` and the other one dominates:

| limb | source | config | rows tripped |
|---|---|---|---:|
| `spread_r_exceeds_selected_cell_limit` | `broker_net_cost_engine.py:859-866` | `selected_cell_pretrade_max_spread_r: 0.10` (`config/agent_config.yaml:715`) | **17,258 (62.40%)** |
| `total_cost_r_exceeds_limit` | `broker_net_cost_engine.py:923-927` | `selected_cell_pretrade_max_total_cost_r: 0.15` (`config/agent_config.yaml:716`) | 20,074 (72.58%) |

Decomposing the **20,448 refusals**: spread-only **374**, total-only **3190**, **both 16884**. The spread cap alone binds **84.4%** of all refusals, and spread is
exactly the term measured overcharged 7.3-8.5x. Pricing that overcharge against the gates:

| spread divided by | candidates PASSING both gates | share | vs shipped |
|---|---:|---:|---:|
| shipped (1.0x) | 7,210 | 26.07% | 1.00x |
| 2.0x | 10,205 | 36.90% | 1.42x |
| 4.0x | 13,492 | 48.78% | 1.87x |
| 7.3x | 16,444 | 59.45% | 2.28x |
| 8.5x | 17,149 | 62.00% | 2.38x |
| spread -> 0 (bound) | 22,488 | 81.31% | 3.12x |

At the measured 7.3x the pass rate goes **26.07% -> 59.45%, a 2.28x increase** — which independently
reproduces the established "fixing costs makes the system trade ~2.2-2.4x MORE" from twelve full
month-replays. The gate model in this dictionary is therefore validated against known ground truth.

**0.3 — `final_blocker_class` is a substring cascade with fixed precedence, not a causal attribution.**
`moonshot_scheduler_v4_best_trade_allocator.py:14265-14349` tests reason text in a fixed order and returns the
first match. `cost_authority` is checked **first**; `fill_realism` at `:14349` is the **fallthrough default**
(so its 148 rows mean "nothing matched", not "fill realism blocked it"). A second classifier at
`order_blocker_precedence.py:172-188` ranks `cost_authority` at **1**, second only to source authority, so
whenever a candidate carries several co-blockers **cost wins the tie-break by construction**. The raw ledger's
`package_replay_order_executable_final_co_blockers` (`v4_timewarp:13692`) is **not projected into the pool**, so
the pool cannot tell you what else would have blocked a row. **Treat 73.93% as an upper bound on cost's causal role.**
Use `miss_reason` (32 values) when you need causality.

**0.4 — Only 29 of 78 fields are trustworthy. 19 carry no information at all.**

| trust class | fields | meaning |
|---|---:|---|
| `TRUST` | 29 | Measured, populated, and free of the frozen-cost defect. Use directly. |
| `CONTAMINATED` | 9 | Inherits the 7.3-8.5x spread overcharge (or a value derived from it). Never use as an economic truth without restating the cost term. |
| `DEGENERATE` | 15 | Populated but an exact duplicate of another column, or collapses to <=2 effective states. |
| `CONSTANT` | 14 | One value across all 27,658 rows. Carries zero information; cannot condition anything. |
| `DIAGNOSTIC` | 6 | Replay bookkeeping. No live code path reads it; it exists to make the ledger auditable. |
| `UNPOPULATED` | 5 | 100% null in this pool. The field exists in the schema and was never written. |

**0.5 — Five exact-duplicate column pairs, verified at 1e-12 over all 27,658 rows.** Using both members of a
pair as "two features" is double-counting:
`cost_r == expected_cost_r` | `candidate_ev_r == expectancy_r` | `fill_probability == entry_quality_fill_probability`
| `execution_fill_probability == limit_fillability_probability` | `direction == side`.
Three further families collapse 1:1: `origin_family == framework == route_family` and
`session_bucket == authority_session == kill_zone`.

**0.6 — `execution_fill_probability` is NOT a flat 0.92.** The brief states it is constant. Measured: **7,400
distinct values**, range 0.0401..0.95, mean 0.8051, 152 nulls. `0.92` covers **19,452 rows (70.32%)** and is the
value of the `limit_marketable` branch at `poi_execution_lifecycle.py:174-176`, not a global constant.
What IS constant: `expected_slippage_r` (0.02), `candidate_confidence` (0.55), `source_completeness` (1.0),
`fill_realism_executable`/`entry_fill_executable` (both True), `dynamic_geometry_policy`, `decision_timeframe`.

---

## 1. POOL SCHEMA — all 78 fields

Source: `docs/audits/.../phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`, n = **27,658**, January 2026, true UTC.
`null` = null rate. `card` = distinct non-null values. Source lines are `src/`-relative and were located
against this worktree's HEAD.

### 1.1 IDENTITY & MECHANISM

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `symbol` | str | 0.00% | 24 | XAUUSD 8.5%; UK100 7.3%; SPX500 7.0% (+21 more) | `TRUST` | v4_timewarp_simulated_live_research_loop.py:251-278 (surface); components/ai_call_policy.py:195 |
| `direction` | str | 0.00% | 2 | SHORT 54.8%; LONG 45.2% | `DEGENERATE` | components/ai_decision_trace_logger.py:73 |
| `origin_family` | str | 0.00% | 10 | current_fvg_fill 25.8%; liquidity_sweep_reclaim 16.2%; displacement_continuation 16.2% (+7 more) | `TRUST` | components/broader_origin_generators.py:442 |
| `framework` | str | 0.00% | 10 | fvg_fill 25.8%; origin_liquidity_sweep_rec 16.2%; origin_displacement_contin 16.2% (+7 more) | `DEGENERATE` | components/ai_decision_trace_logger.py:175 |
| `route_family` | str | 0.00% | 10 | current_fvg_fill 25.8%; liquidity_sweep_reclaim 16.2%; displacement_continuation 16.2% (+7 more) | `DEGENERATE` | components/gtos_vnext_runtime.py:297 |
| `setup_family` | null | 100.00% | 0 | (all null) | `UNPOPULATED` | research_infra/forward_capture.py:2488 |
| `bucket_source_family` | null | 100.00% | 0 | (all null) | `UNPOPULATED` | moonshot_scheduler_v4_best_trade_allocator.py:22766 |
| `dynamic_geometry_policy` | str | 0.00% | 1 | momentum_exhaustion 100.0% | `CONSTANT` | components/selector_v4.py:2762 |
| `selected_policy_for_expected_net_r` | str | 0.00% | 1 | momentum_exhaustion 100.0% | `CONSTANT` | moonshot_scheduler_v4_best_trade_allocator.py:3421 |
| `decision_timeframe` | str | 0.00% | 1 | M15 100.0% | `CONSTANT` | components/ultimate_candidate_package.py:2935 |
| `market_timeframe` | str | 0.00% | 1 | M15 100.0% | `CONSTANT` | components/broader_origin_generators.py:1944 |
| `candidate_id` | str | 0.00% | 21880 | broadorigin_9989cfae03a177 0.5%; broadorigin_f477b177a285a0 0.5%; broadorigin_f772f018187716 0.2% (+21877 more) | `TRUST` | components/broader_origin_generators.py (emitted per candidate); projected b7_5_diagnostic_pool.py:180 |
| `decision_time_utc` | str | 0.00% | 1969 | 2026-01-09T13:45:00+00:00 0.2%; 2026-01-23T07:45:00+00:00 0.2%; 2026-01-13T13:45:00+00:00 0.2% (+1966 more) | `TRUST` | components/broader_origin_generators.py:1144 |
| `side` | str | 0.00% | 2 | SHORT 54.8%; LONG 45.2% | `DEGENERATE` | components/broader_origin_generators.py:590 |

**`symbol`** — Instrument, 24 values (GTOS_24_SYMBOL_SURFACE).

**`direction`** — LONG/SHORT. Exact duplicate of `side` on all 27,658 rows.
  - Identical to `side`, n=27,658, zero mismatches.

**`origin_family`** — The generating mechanism, 10 values. THE primary conditioning axis of this pool.

**`framework`** — `origin_<origin_family>`. A prefixed restatement of origin_family, 10 values.
  - 1:1 with origin_family.

**`route_family`** — Route-level family label, 10 values, 1:1 with origin_family in this pool.
  - 1:1 with origin_family.

**`setup_family`** — Sleeve-level setup family.
  - 100% null. Never written on the broad-V4 path.

**`bucket_source_family`** — Bucket provenance family.
  - 100% null.

**`dynamic_geometry_policy`** — Geometry policy selected for the candidate.
  - `momentum_exhaustion` on all 27,658 rows.

**`selected_policy_for_expected_net_r`** — Policy used to compute expected_net_r.
  - `momentum_exhaustion` on all 27,658 rows. The policy axis is DEAD in this arm - S0 means fixed selection.

**`decision_timeframe`** — Decision cadence.
  - M15 on all rows.

**`market_timeframe`** — Market data timeframe.
  - M15 on all rows.

**`candidate_id`** — Generator-assigned candidate handle, prefix `broadorigin_`. NOT a primary key.
  - W0-F1: 21,880 distinct ids over 27,658 rows; 967 ids repeat, max 140x; 24.39% of rows sit on a repeated id. Join on (candidate_id, decision_time_utc) - w0_ws.key().

**`decision_time_utc`** — UTC timestamp of the decision window that emitted the candidate. 1,969 distinct = the M15 grid over January.
  - TRUE UTC in this pool (CJ re-clock). The pre-CJ pools (CD_REPAIRED_*) are true UTC + 2h. Never mix the two.

**`side`** — LONG/SHORT. Exact duplicate of `direction`.
  - Identical to `direction`, n=27,658.

### 1.2 TIME & SESSION

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `session_bucket` | str | 0.00% | 27 | ny 16.8%; london 16.6%; moonshot_h06_07 5.1% (+24 more) | `TRUST` | components/broader_origin_generators.py:1939 |
| `authority_session` | str | 0.00% | 27 | ny 17.8%; london 17.6%; tokyo 4.7% (+24 more) | `DEGENERATE` | v4_timewarp_simulated_live_research_loop.py:9626 |
| `kill_zone` | str | 0.00% | 27 | ny 17.8%; london 17.6%; tokyo 4.7% (+24 more) | `DEGENERATE` | components/ai_call_policy.py:196 |
| `route_session` | str | 0.00% | 4 | off_configured_session 59.9%; ny 17.8%; london 17.6% (+1 more) | `TRUST` | components/broader_origin_generators.py:1937 |
| `utc_hour_bucket` | str | 0.00% | 24 | h07_08 6.5%; h14_15 6.3%; h08_09 6.2% (+21 more) | `TRUST` | components/broader_origin_generators.py:1934 |

**`session_bucket`** — Session label, 27 values, `moonshot_hHH_HH` form. Derived from the decision hour.
  - Re-derived on true UTC by CJ. The authoritative B_TIME map is phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json - all 83 cells negative. AW's older map is superseded.

**`authority_session`** — Session under authority semantics. Identical to session_bucket here (27 values).
  - 1:1 with session_bucket and kill_zone.

**`kill_zone`** — Kill-zone label. Identical to session_bucket here (27 values).
  - 1:1 with session_bucket.

**`route_session`** — Configured route session: off_configured_session 59.88%, ny 17.79%, london 17.60%, tokyo 4.73%.
  - 59.88% of the pool is generated OUTSIDE any configured session. Those rows are what selector_reason=admission_quality_off_configured_session_entry_blocked acts on (1,079 rows).

**`utc_hour_bucket`** — `hHH_HH` hour bucket, 24 values.
  - True UTC after the CJ re-clock.

### 1.3 COST

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `spread_r` | float | 0.00% | 26111 | 0 .. 18.729 (mean 0.56421) | `CONTAMINATED` | components/broker_net_cost_engine.py:298-306 (spread_r = spread_price / sl_distance), packed at :318 and :748 |
| `cost_r` | float | 0.00% | 26575 | 0.023637 .. 18.776 (mean 0.66316) | `CONTAMINATED` | components/broker_net_cost_engine.py:700-706; packet key :774 |
| `expected_cost_r` | float | 0.00% | 26575 | 0.023637 .. 18.776 (mean 0.66316) | `DEGENERATE` | components/execution.py:7817 |
| `commission_r` | float | 0.00% | 15539 | 0 .. 1.355 (mean 0.065224) | `TRUST` | components/broker_net_cost_engine.py:695, :757 |
| `swap_cost_r` | float | 0.00% | 18850 | 0 .. 0.70924 (mean 0.013723) | `TRUST` | components/broker_net_cost_engine.py:768, :778; daily->horizon at :437/:450 |
| `expected_slippage_r` | float | 0.00% | 1 | const 0.02 | `CONSTANT` | components/broker_net_cost_engine.py:653, :772 |
| `fallback_execution_surcharge_r` | float | 0.00% | 1 | const 0 | `CONSTANT` | replay_acceleration_attempt5_typed_sparse_runner.py:13026 |
| `guarded_market_fallback_extra_cost_r` | float | 0.00% | 1 | const 0 | `CONSTANT` | v4_timewarp_simulated_live_research_loop.py:65075 |
| `old_proxy_vs_broker_calibrated_delta_r` | float | 0.00% | 25973 | -0.16 .. 18.596 (mean 0.43113) | `DIAGNOSTIC` | v4_timewarp_simulated_live_research_loop.py:3383 |
| `broker_pretrade_cost_executable` | bool | 0.00% | 2 | false 73.9%; true 26.1% | `DEGENERATE` | v4_timewarp_simulated_live_research_loop.py:69968 |
| `broker_pretrade_diag_expected_cost_r` | float | 26.07% | 19603 | 0.12035 .. 18.776 (mean 0.86632) | `CONTAMINATED` | replay_acceleration_attempt5_typed_sparse_runner.py:2383 |
| `commission_r_broker_true_measured` | null | 100.00% | 0 | (all null) | `UNPOPULATED` | research_infra/train_engine/cuts.py:865 |
| `commission_r_repair_status` | null | 100.00% | 0 | (all null) | `UNPOPULATED` | research_infra/train_engine/cuts.py:866 |
| `swap_horizon_repair_status` | null | 100.00% | 0 | (all null) | `UNPOPULATED` | research_infra/train_engine/cuts.py:868 |
| `pretrade_cost_packet_status` | str | 0.00% | 2 | REFUSED 73.9%; PASSED 26.1% | `TRUST` | components/broker_net_cost_engine.py:842 ('REFUSED' if reasons else 'PASSED'); reasons built :846-928; selector_v4.py:1845 |

**`spread_r`** — Half-spread cost in R: |ask-bid| / sl_distance.
  - THE dominant cost term: mean 0.5642 R of a 0.6632 R total = 85.1%.
  - Overcharged 7.3-8.5x (measured on both January and March). The error is in the bid/ask the replay feeds, not in this division.
  - Gate-critical: `selected_cell_pretrade_max_spread_r` = 0.10 (config/agent_config.yaml:715). 17,258 rows (62.4%) exceed it.

**`cost_r`** — Total pretrade cost in R = spread_r + expected_slippage_r + swap_cost_r + commission_r.
  - mean 0.6632 R, max 18.78 R. Compare with the 0.15 R gate: 20,074 rows (72.6%) exceed it.
  - 85.1% of it is the 7.3-8.5x-overcharged spread term.
  - Exact duplicate of expected_cost_r on all 27,658 rows.

**`expected_cost_r`** — Same number as cost_r.
  - |cost_r - expected_cost_r| < 1e-12 on all 27,658 rows.

**`commission_r`** — Broker-true commission in R.
  - mean 0.0652 R = 9.8% of total cost. Range 0..1.355. This term is broker-true and is NOT part of the spread defect.

**`swap_cost_r`** — Overnight financing in R over the assumed holding horizon.
  - mean 0.0137 R = 2.1% of total cost. Smallest term. Horizon assumption is the risk here, not the rate.

**`expected_slippage_r`** — Flat slippage allowance.
  - EXACTLY 0.02 on all 27,658 rows. src/research_infra/divergence_matrix.py:366 already records that this flat 0.02 covers only 80.3% of a measured +0.539109 R slippage distribution.

**`fallback_execution_surcharge_r`** — Surcharge when execution falls back to a guarded market order.
  - EXACTLY 0.0 on all 27,658 rows - the fallback never fired in this arm.

**`guarded_market_fallback_extra_cost_r`** — Extra cost of the guarded-market fallback.
  - EXACTLY 0.0 on all 27,658 rows.

**`old_proxy_vs_broker_calibrated_delta_r`** — Difference between the legacy cost proxy and the broker-calibrated packet.
  - mean +0.4311 R, range -0.16..+18.60. Positive = broker-calibrated charges MORE than the legacy proxy. Reconciliation aid only.

**`broker_pretrade_cost_executable`** — Boolean: did the pretrade cost packet pass?
  - EXACT identity, n=27,658: False <=> pretrade_cost_packet_status=='REFUSED' <=> final_blocker_class=='cost_authority'. 20,448 False / 7,210 True. Three columns, ONE bit.

**`broker_pretrade_diag_expected_cost_r`** — Diagnostic expected cost for rows the packet refused.
  - 26.07% null - null exactly on the 7,210 PASSED rows. mean 0.8663 R on the refused ones.

**`commission_r_broker_true_measured`** — Broker-true measured commission, repair field.
  - 100% null in January.

**`commission_r_repair_status`** — Status of the commission repair.
  - 100% null in January.

**`swap_horizon_repair_status`** — Status of the swap-horizon repair.
  - 100% null in January.

**`pretrade_cost_packet_status`** — REFUSED (73.93%) / PASSED (26.07%).
  - THE headline gate. Two independent limbs both fire here: spread_r > max_spread_r (:864-866) and total_cost_r > max_total_cost_r (:927).
  - MEASURED SPLIT of the 20,448 refusals: spread-only 374 (1.4%), total-only 3,190 (15.6%), BOTH 16,884 (82.6%). The spread cap alone binds 17,258 = 84.4% of refusals.

### 1.4 BELIEF / EV

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `candidate_probability` | float | 0.00% | 26844 | 0.5843 .. 0.96629 (mean 0.76576) | `CONTAMINATED` | components/ultimate_candidate_package.py:1727, :2988 |
| `candidate_ev_r` | float | 0.00% | 26892 | 0.39849 .. 1.3888 (mean 0.86675) | `CONTAMINATED` | components/ultimate_candidate_package.py:1724, :2985 |
| `expectancy_r` | float | 0.00% | 26892 | 0.39849 .. 1.3888 (mean 0.86675) | `DEGENERATE` | components/ultimate_book/convergence_advisory.py:32 |
| `expected_net_r` | float | 0.00% | 27087 | -18.169 .. 1.3584 (mean 0.20359) | `CONTAMINATED` | components/executable_value_semantics.py:114; learned_edge_layer_v4.py:469 (p_fill * net_r_value) |
| `candidate_confidence` | float | 0.00% | 1 | const 0.55 | `CONSTANT` | components/selector_v4.py:3316 |
| `confidence_default_applied` | bool | 0.00% | 1 | true 100.0% | `CONSTANT` | components/ultimate_candidate_package.py:1776 |
| `source_completeness` | float | 0.00% | 1 | const 1 | `CONSTANT` | components/broader_origin_generators.py:1925 |
| `source_bound_signal_r` | float | 0.00% | 125 | 0 .. 2.6928e+05 (mean 76683) | `DIAGNOSTIC` | v4_timewarp_simulated_live_research_loop.py:21215, :34383 |
| `matched_sleeve_count` | float | 0.00% | 6 | 0 .. 5 (mean 1.1866) | `TRUST` | components/live_decision_packet_v4.py:486 |
| `effective_admission_count` | float | 0.00% | 3 | 0 .. 2 (mean 0.59961) | `TRUST` | moonshot_scheduler_v4_best_trade_allocator.py:6181 |

**`candidate_probability`** — The model's win probability for this candidate. Range 0.5843..0.9663, mean 0.7658.
  - CALIBRATION DEFECT: mean predicted 0.7658 against a MEASURED gross win rate of 0.3468 - the belief layer is over-confident by a factor of 2.21x and never sees a return.
  - Minimum predicted probability is 0.5843: the generator never emits a candidate it believes is worse than a coin flip.

**`candidate_ev_r`** — Expected R before cost. Range 0.3985..1.3888, mean 0.8668.
  - Every single row has candidate_ev_r > 0 (min +0.3985). Against a measured pool gross mean of -0.2175 R. The EV layer is never negative and is wrong in level by ~1.08 R/trade.

**`expectancy_r`** — Same number as candidate_ev_r.
  - |candidate_ev_r - expectancy_r| < 1e-12 on all 27,658 rows.

**`expected_net_r`** — candidate_ev_r after cost and fill weighting. Range -18.169..+1.358, mean +0.2036.
  - This is the only belief field that can go negative, and it does so ONLY because the contaminated cost_r is subtracted. Its negative tail (-18.17) is the spread overcharge, not a belief.

**`candidate_confidence`** — Sleeve confidence weight.
  - EXACTLY 0.55 on all 27,658 rows - the default, not a learned value. See confidence_default_applied.

**`confidence_default_applied`** — Was the confidence a filled-in default?
  - TRUE on all 27,658 rows. Confirms candidate_confidence carries no per-candidate information anywhere in this pool.

**`source_completeness`** — Fraction of required source inputs present.
  - EXACTLY 1.0 on all 27,658 rows.

**`source_bound_signal_r`** — Summed source-bound signal magnitude. Range 0..269,276, mean 76,683.
  - Only 125 distinct values over 27,658 rows - it is a package-level aggregate replicated onto members, not a per-candidate quantity. Magnitudes are not R despite the `_r` suffix.

**`matched_sleeve_count`** — How many book sleeves matched this candidate. 0..5, mean 1.187.

**`effective_admission_count`** — How many sleeves actually admitted it. 0..2, mean 0.600.
  - Never exceeds 2 anywhere in the pool although matched_sleeve_count reaches 5.

### 1.5 FILL

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `fill_probability` | float | 0.00% | 23813 | 0.65885 .. 0.95 (mean 0.89232) | `CONTAMINATED` | components/poi_execution_lifecycle.py:192-199; learned_edge_layer_v4.py:475 |
| `entry_quality_fill_probability` | float | 0.00% | 23813 | 0.65885 .. 0.95 (mean 0.89232) | `DEGENERATE` | components/selector_v4.py:3054 |
| `execution_fill_probability` | float | 0.55% | 7399 | 0.040133 .. 0.95 (mean 0.80506) | `CONTAMINATED` | components/poi_execution_lifecycle.py:174-178 (marketable branch = 0.92); :407; selector_v4.py:512 |
| `limit_fillability_probability` | float | 0.55% | 7399 | 0.040133 .. 0.95 (mean 0.80506) | `DEGENERATE` | components/broader_origin_generators.py:1308 |
| `effective_order_type` | str | 0.00% | 2 | limit 83.5%; none 16.5% | `TRUST` | v4_timewarp_simulated_live_research_loop.py:88003, :88298 |
| `fill_realism_class` | str | 0.00% | 2 | passive_queue_confirmed 76.1%; source_safe_immediate_mark 23.9% | `TRUST` | v4_timewarp_simulated_live_research_loop.py:60447 |
| `fill_realism_executable` | bool | 0.00% | 1 | true 100.0% | `CONSTANT` | v4_timewarp_simulated_live_research_loop.py:60448 |
| `entry_fill_executable` | bool | 0.00% | 1 | true 100.0% | `CONSTANT` | v4_timewarp_simulated_live_research_loop.py:2184 |
| `limit_marketable_at_decision` | bool | 85.19% | 2 | None 85.2%; True 11.5%; False 3.3% | `DIAGNOSTIC` | components/poi_execution_lifecycle.py:224 |

**`fill_probability`** — Entry-quality fill probability. Range 0.6589..0.95, mean 0.8923.
  - NEVER validated against an outcome. Zero rows in this pool score as 'did not fill' - every candidate is walked as a filled trade regardless of this number.
  - W0-F2 measured the real cost of that: requiring the entry limit to actually trade moves the pool from +0.0409 to -0.2367 R/trade - the fill-blind convention manufactures +0.2776 R/trade.

**`entry_quality_fill_probability`** — Same number as fill_probability.
  - Identical to fill_probability on all 27,658 rows.

**`execution_fill_probability`** — Execution-side fill probability. 7,400 distinct values, range 0.0401..0.95, mean 0.8051, 0.55% null.
  - CORRECTION to the swarm brief: this is NOT a flat constant. 0.92 covers 19,452 rows (70.3%) - it is the value of the `limit_marketable` branch at poi_execution_lifecycle.py:175-176 - but 7,400 distinct values exist and the field ranges down to 0.0401.
  - 152 rows (0.55%) are null.

**`limit_fillability_probability`** — Same number as execution_fill_probability.
  - Identical to execution_fill_probability (including nulls) on all 27,658 rows.

**`effective_order_type`** — `limit` 23,106 (83.54%) / `none` 4,552 (16.46%).
  - 4,552 rows never got an order type at all - they died before order shaping. Any fill-mechanics question must exclude them.

**`fill_realism_class`** — `passive_queue_confirmed` 21,052 (76.12%) / `source_safe_immediate_marketable` 6,606 (23.88%).
  - This is the closest thing in the pool to 'would the limit have filled', and it is a CLASSIFICATION, not an observation - it is never checked against the path.

**`fill_realism_executable`** — Did fill realism permit execution?
  - TRUE on all 27,658 rows.

**`entry_fill_executable`** — Was the entry fillable?
  - TRUE on all 27,658 rows. Combined with the row above: the pool asserts every candidate was fillable and never tests it.

**`limit_marketable_at_decision`** — Was the limit price already marketable when the decision was taken?
  - 85.19% NULL (23,563 rows). Only 3,175 True / 920 False. The single most important fill question in the pool is UNANSWERED on 6 of every 7 rows.
  - Populated exactly on the 4,095 scheduler_option_materialized rows - it is written during scheduler materialization, so rows that die earlier never get it.

### 1.6 ADMISSION & BLOCKING

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `selector_action` | str | 0.00% | 5 | reject 83.2%; open-reduced-risk 13.5%; reduce-risk 2.7% (+2 more) | `TRUST` | components/gtos_vnext_runtime.py:1699 |
| `selector_reason` | str | 0.00% | 11 | broker_net_pretrade_cost_p 50.3%; broker_net_admission_ev_ne 23.3%; source_bound_router_refusa 13.5% (+8 more) | `TRUST` | components/selector_v4.py:3592; refusal appends :3832 (ev), :3843 (cost), :3960/:4500 (sleeve), :2556/:4412 (off-session) |
| `effective_selector_action` | str | 0.00% | 5 | reject 85.6%; open-reduced-risk 11.4%; reduce-risk 2.5% (+2 more) | `TRUST` | moonshot_scheduler_v4_best_trade_allocator.py:11402 |
| `effective_selector_reason` | str | 0.00% | 12 | broker_net_pretrade_cost_p 50.3%; broker_net_admission_ev_ne 23.3%; source_bound_router_refusa 13.5% (+9 more) | `TRUST` | moonshot_scheduler_v4_best_trade_allocator.py:11413 |
| `admission_risk_class` | str | 0.00% | 5 | reject 85.6%; open-reduced-risk 11.4%; reduce-risk 2.5% (+2 more) | `TRUST` | projected b7_5_diagnostic_pool.py:247 (no direct writer in src/ - assembled from the admission packet) |
| `risk_finalizer_rank` | int | 0.00% | 140 | 1 .. 149 (mean 37.499) | `TRUST` | v4_timewarp_simulated_live_research_loop.py:28810 (probe.get('rank')) |
| `risk_finalizer_reason` | str | 0.00% | 18 | broker_cost_authority_bloc 73.9%; package_executable_authori 14.8%; scheduler_option_status_no 5.8% (+15 more) | `TRUST` | v4_timewarp_simulated_live_research_loop.py:28813 |
| `miss_reason` | str | 0.00% | 32 | scheduler_materialization_ 73.9%; scheduler_vetoed_candidate 7.5%; scheduler_vetoed_candidate 5.2% (+29 more) | `TRUST` | v4_timewarp_simulated_live_research_loop.py:92629; v4_know_it_all_live_replay_runtime.py:909 |
| `candidate_lifecycle_action` | str | 0.00% | 4 | not_evaluated_selector_not 82.9%; new_position 16.3%; source_required_fail_close 0.6% (+1 more) | `TRUST` | v4_timewarp_simulated_live_research_loop.py:3135 |
| `final_blocker_class` | str | 0.00% | 9 | cost_authority 73.9%; other 9.7%; package_authority 9.6% (+6 more) | `DIAGNOSTIC` | Classified by _order_executable_final_blocker_class moonshot_scheduler_v4_best_trade_allocator.py:14265-14349; carried to the row at v4_timewarp:15391 / :13686 |

**`selector_action`** — reject 83.22% / open-reduced-risk 13.53% / reduce-risk 2.69% / source-required 0.47% / trade 0.08% (21 rows).
  - Only 21 of 27,658 candidates were selected to trade, and even those never reached headline execution (see the pool-population caveat).

**`selector_reason`** — 11 values. Top: broker_net_pretrade_cost_packet_refused 50.28%, broker_net_admission_ev_negative_after_cost 23.33%, source_bound_router_refusal 13.53%.
  - 73.61% of all selector rejections are cost-derived (50.28% packet refusal + 23.33% EV-negative-after-cost). BOTH limbs consume the contaminated cost_r.

**`effective_selector_action`** — Selector action after downstream softening.
  - Differs from selector_action on 1,054 rows (3.81%).

**`effective_selector_reason`** — 12 values; superset of selector_reason.

**`admission_risk_class`** — reject 85.56% / open-reduced-risk 11.41% / reduce-risk 2.49% / source-required 0.47% / trade 0.07% (20 rows).
  - Near-duplicate of selector_action but NOT identical: 20 'trade' vs 21. One candidate the selector said trade, admission did not.

**`risk_finalizer_rank`** — Rank assigned by the risk finalizer, 1..149, mean 37.5.
  - Populated on all rows including ones that never reached the finalizer - treat rank on a cost-refused row as a probe artifact.

**`risk_finalizer_reason`** — 18 values. broker_cost_authority_blocked_non_executable 73.93%, package_executable_authority_required_not_met 14.81%.

**`miss_reason`** — 32 values, the finest-grained blocking label in the pool.
  - Use this instead of final_blocker_class when you need causality - it is the raw reason text the cascade classifies.

**`candidate_lifecycle_action`** — not_evaluated_selector_not_risk_bearing 82.95% / new_position 16.31% / source_required 0.61% / replace_pending 0.13%.
  - 4,512 rows (16.31%) reached `new_position` - the largest honest 'this would have been an order' population in the pool.

**`final_blocker_class`** — 9 values. The single most-used field in this investigation. cost_authority 73.93%.
  - *** THIS IS A SUBSTRING CASCADE WITH FIXED PRECEDENCE, NOT A CAUSAL ATTRIBUTION. ***
  - Order of checks (first match wins): cost_authority -> selector_materialization -> scheduler_selection -> package_authority -> marketable_guard -> stop_hazard -> daily_lockout -> headroom -> lifecycle_authority -> risk_basis_missing -> lifecycle_expiry -> fill_realism.
  - `fill_realism` (148 rows) is the FALLTHROUGH DEFAULT at :14349 - it means 'no pattern matched', NOT 'fill realism blocked it'.
  - A second classifier, order_blocker_precedence.py:172-188, ranks cost_authority at 1 (second only to source authority) and `other` at 8. Whenever a candidate carries several co-blockers, cost wins the tie-break BY CONSTRUCTION.
  - The raw ledger carries `package_replay_order_executable_final_co_blockers` (v4_timewarp:13692) - it is NOT projected into the pool, so the pool cannot tell you what ELSE would have blocked a row. The 73.93% cost share is therefore an UPPER BOUND on cost's causal role.

### 1.7 SCHEDULER

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `scheduler_materialization_status` | str | 0.00% | 2 | not_scheduler_ranked 85.2%; scheduler_option_materiali 14.8% | `TRUST` | v4_timewarp_simulated_live_research_loop.py:27862 |
| `scheduler_selection_disposition` | str | 0.00% | 3 | candidate_materialization_ 85.2%; candidate_generated_not_sc 14.1%; scheduler_preselected_then 0.7% | `TRUST` | v4_timewarp_simulated_live_research_loop.py:27855 |

**`scheduler_materialization_status`** — not_scheduler_ranked 85.19% / scheduler_option_materialized 14.81% (4,095 rows).
  - Exactly matches the non-null count of limit_marketable_at_decision (4,095). The scheduler is where the fill fields get written.

**`scheduler_selection_disposition`** — candidate_materialization_skipped_before_scheduler 85.19% / candidate_generated_not_scheduler_selected 14.10% / scheduler_preselected_then_rejected_by_finalizer 0.71% (196 rows).
  - Only 196 candidates in the whole month got as far as the finalizer and were then rejected.

### 1.8 GEOMETRY

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `entry_price` | float | 0.00% | 12981 | 0.57145 .. 97602 (mean 13831) | `TRUST` | components/be_shadow_logger.py:112 (logging); shaped on the generator path |
| `stop_loss` | float | 0.00% | 26597 | 0.57085 .. 98044 (mean 13834) | `TRUST` | components/be_shadow_logger.py:113 |
| `take_profit_1` | float | 0.00% | 26608 | 0.5651 .. 99693 (mean 13825) | `TRUST` | components/broader_origin_generators.py:1909 |
| `policy_target_r` | float | 0.00% | 1231 | 1.131 .. 505.47 (mean 2.0958) | `DIAGNOSTIC` | v4_timewarp_simulated_live_research_loop.py:88931, :3403 |
| `raw_target_r` | float | 0.00% | 1232 | 1.131 .. 505.47 (mean 2.0959) | `DIAGNOSTIC` | v4_timewarp_simulated_live_research_loop.py:88504, :88927 |
| `risk_per_trade_pct` | float | 0.00% | 4 | 0.25 .. 2 (mean 1.1545) | `TRUST` | components/orchestrator.py:14097; v4_timewarp:7673 |

**`entry_price`** — Limit entry price. Only 12,981 distinct over 27,658 rows.
  - W0-F2: 55.2% of blind target-first paths reach +2R BEFORE this price is ever traded. Entry is systematically on the far side of the market.

**`stop_loss`** — Stop price. risk_distance = |entry_price - stop_loss| is the R denominator for the whole investigation.

**`take_profit_1`** — First target price.
  - Implies EXACTLY 2.0000 R on every one of the 27,658 rows. The declared contract is uniformly 2R.

**`policy_target_r`** — Target in R after policy shaping. Range 1.131..505.471, mean 2.096.
  - W0-F4: disagrees with the take_profit_1-implied 2.0R on 1,229 rows (4.44%), reaching 505R. 85% of those are current_breaker_re_entry - the family CQ's inverted-breaker candidate is built from. Prefer the price-implied 2.0R; mitigate with w0_ws.bars_to_fav(row, 2.0).

**`raw_target_r`** — Target in R before policy shaping. 1,232 distinct.
  - Equals policy_target_r on all 1,229 mismatch rows - the shaping is a no-op there.

**`risk_per_trade_pct`** — Risk budget: 2.0% 39.08% / 0.5% 35.67% / 1.0% 17.53% / 0.25% 7.73%.
  - Four discrete values. This is the sizing axis; it does NOT affect any R-denominated column in this pool.

### 1.9 EXPOSURE CONTEXT

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `same_symbol_lifecycle_action` | str | 0.00% | 4 | new_position 99.0%; source_required_fail_close 0.9%; replace_pending 0.2% (+1 more) | `DEGENERATE` | components/broker_order_lifecycle_capture_v4.py:245 |
| `same_symbol_exposure_risk_pct` | float | 0.00% | 2 | 0 .. 0.1 (mean 0.00073758) | `DEGENERATE` | moonshot_scheduler_v4_best_trade_allocator.py:21897 |
| `same_side_pending_risk_pct` | float | 0.00% | 2 | 0 .. 0.1 (mean 6.1465e-05) | `DEGENERATE` | moonshot_scheduler_v4_best_trade_allocator.py:21858 |
| `opposite_pending_risk_pct` | float | 0.00% | 2 | 0 .. 0.1 (mean 6.8696e-05) | `DEGENERATE` | moonshot_scheduler_v4_best_trade_allocator.py:21865 |

**`same_symbol_lifecycle_action`** — new_position 98.97% / source_required_fail_closed 0.86% / replace_pending 0.16% / no_trade_duplicate 0.01% (3 rows).
  - 98.97% one value.

**`same_symbol_exposure_risk_pct`** — Existing same-symbol exposure.
  - Only two values: 0.0 and 0.1. Nonzero on 0.74% of rows.

**`same_side_pending_risk_pct`** — Pending same-side risk.
  - Only 0.0 / 0.1; nonzero on 0.06%.

**`opposite_pending_risk_pct`** — Pending opposite-side risk.
  - Only 0.0 / 0.1; nonzero on 0.07%.

### 1.10 OUTCOME

| field | dtype | null | card | range / top | trust | written at |
|---|---|---:|---:|---|---|---|
| `opportunity_net_proxy_r` | float | 0.00% | 25707 | -19.776 .. 10.614 (mean -0.88066) | `CONTAMINATED` | v4_timewarp_simulated_live_research_loop.py:92730, :93122 |
| `missed_opportunity_r_scoreability_status` | str | 0.00% | 1 | diagnostic_opportunity_r_s 100.0% | `CONSTANT` | v4_timewarp_simulated_live_research_loop.py:28156 (set at :28142-28146); projected b7_5_diagnostic_pool.py:339 |
| `missed_opportunity_non_executable_diagnostic_scoreable` | bool | 0.00% | 1 | true 100.0% | `CONSTANT` | v4_timewarp_simulated_live_research_loop.py:28153; b7_5_diagnostic_pool.py:338 |

**`opportunity_net_proxy_r`** — THE outcome column. Counterfactual net R the candidate would have earned, AFTER subtracting cost_r. Mean -0.8807, range -19.776..+10.614.
  - Cost is already subtracted using the 7.3-8.5x-overcharged spread. NEVER quote this as the signal.
  - Use gross_r = opportunity_net_proxy_r + cost_r (working set) - an exact algebraic inverse of the engine's own subtraction, so it is CLEAN of the cost defect. Gross mean is -0.2175 R.

**`missed_opportunity_r_scoreability_status`** — Scoreability tier.
  - `diagnostic_opportunity_r_scoreable` on ALL 27,658 rows - BY CONSTRUCTION, because that is the filter that built the pool.
  - *** POOL-POPULATION CAVEAT: the gate at v4_timewarp:28130-28140 requires `not headline_r_scoreable`. The pool is therefore 100% COUNTERFACTUAL - it contains ZERO executed trades. The raw ledger holds 153,425 rows; the pool is the 27,658 (18.03%) that are diagnostic-scoreable. ***

**`missed_opportunity_non_executable_diagnostic_scoreable`** — Boolean twin of the status above.
  - TRUE on all 27,658 rows.

---

## 2. TRUSTWORTHY vs CONTAMINATED

### 2.1 The frozen-cost defect: exactly which fields inherit it

The overcharge lives in **one** term — `spread_r` — computed at `broker_net_cost_engine.py:298-306` as
`spread_r = |ask - bid| / sl_distance`. The division is correct; the `ask`/`bid` the replay feeds are not.
`spread_r` is **mean 0.5642 R of a 0.6632 R total cost = 85.07%** of every charge in this pool.

**Inherits the defect (do not quote as economics without restating cost):**

| field | how it inherits |
|---|---|
| `spread_r` | is the defect |
| `cost_r`, `expected_cost_r` | sum containing `spread_r` (`:700-706`) |
| `broker_pretrade_diag_expected_cost_r` | same packet |
| `old_proxy_vs_broker_calibrated_delta_r` | difference against the same packet |
| `expected_net_r` | `candidate_ev_r` minus the contaminated cost; its −18.17 tail IS the overcharge |
| `opportunity_net_proxy_r` | **the outcome column** — cost already subtracted |
| `pretrade_cost_packet_status`, `broker_pretrade_cost_executable`, `final_blocker_class=='cost_authority'`, `selector_reason` cost limbs | the *verdicts* the defect produces |

**Clean of it:**

| field | why |
|---|---|
| `gross_r` (working set) | `= opportunity_net_proxy_r + cost_r`, the exact algebraic inverse of the engine's own subtraction (`w0_build_working_set_v2.py:301`). Adding back the identical `cost_r` cancels the error exactly. Pool gross mean **−0.2175 R**. |
| `commission_r` (mean 0.0652 R), `swap_cost_r` (mean 0.0137 R) | broker-true terms, independent of the spread model |
| all path geometry (`mfe_r`, `mae_r`, `bars_to_*`, `which_came_first`, `r_at_bar_*`) | measured off M1 bars, never touches the cost model |
| all identity, time, session, geometry-price fields | pre-cost |

### 2.2 Contamination that is NOT the cost model

- **Belief calibration.** `candidate_probability` mean **0.7658** against a measured gross win rate of
  **0.3468** — over-confident **2.21x**. Minimum predicted probability is **0.5843**: the generator never
  emits a candidate it believes is worse than a coin flip. `candidate_ev_r` is **positive on every single
  row** (min +0.3985) against a pool gross mean of −0.2175 R. Neither field ever sees a realized return.
- **Fill fiction.** `fill_realism_executable` and `entry_fill_executable` are `True` on all 27,658 rows;
  `fill_probability` is never validated. W0-F2 measured the cost: requiring the entry limit to actually
  trade moves the pool **+0.0409 -> −0.2367 R/trade**, i.e. the fill-blind convention manufactures
  **+0.2776 R/trade** of edge no limit order could capture.
- **`limit_marketable_at_decision` is 85.19% NULL** (23,563 rows). The most important fill question in the
  pool is unanswered on 6 of every 7 rows, and it is answered exactly on the 4,095 rows that reached
  scheduler materialization.
- **`policy_target_r` disagrees with the price geometry on 1,229 rows (4.44%)**, reaching 505R, while
  `take_profit_1` implies exactly 2.0000R on every row. 85% of the disagreements are `current_breaker_re_entry`.

---

## 3. PATHS SCHEMA

`CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` — **27,658 rows, 34.1 MB gz, 12 fields.**

| field | type | meaning |
|---|---|---|
| `schema` | str | `gtos-session-ck-ordered-path-sidecar-v1` |
| `arm_id` | str | `S0R0` |
| `candidate_id` | str | join key part 1 |
| `decision_time_utc` | str | join key part 2 |
| `horizon_end_utc` | str | decision_time + 2h |
| `symbol` | str | instrument |
| `side` | str | LONG/SHORT |
| `source_timeframe` | str | **`M1`** on every row |
| `source_path` | str | e.g. `sources/bars/bridge_ftmo_m1_202601/BTCUSD_M1.csv` |
| `source_sha256` | str | content hash of the bar file |
| `ordered_tick_source` | null | **always null — there is no tick-level path anywhere in this asset** |
| `ordered_path_observations` | list | the bars; each `{open, high, low, close, time_utc}` |

**Bar structure.** Each observation is OHLC + `time_utc`. **There is no volume, no bid/ask and no spread**,
so no within-bar fill or slippage question can be answered from this asset — only price-touch questions.

**Horizon.** The first bar is the M1 bar **after** the decision (decision 00:15:00 -> first bar 00:16:00) and the
last is `decision_time + 2h`. Every path is **<= 120 M1 bars = a hard 2-hour cap**; 86.12% are exactly 120
(mean 116.78, min 3, max 120). **No holding-time or time-stop question beyond 2h is answerable from this pool at all.**

**Join.** Key is `(candidate_id, decision_time_utc)` — *not* `candidate_id`, which repeats (§0.5, W0-F1).
**Coverage is total: 27,658 pool rows / 27,658 sidecar rows / 0 rows without a path / 0 duplicate keys /
0 side-or-symbol mismatches** (`w0_WORKING_SET_BUILD_V2.json`).

**Read the WORKING SET, not this file.** `w0_WORKING_SET.jsonl.gz` (128 cols = 78 pool + 50 derived) loads in
**0.53 s**; `w0_R_PATHS.jsonl.gz` streams bar-level R in **0.68 s**. Streaming the raw 34 MB sidecar is the
15-minute stall that killed four agents. Helper: `w0_ws.py` (`load()`, `key()`, `dedup()`, `walk()`, `bars_to_fav()`).

---

## 4. ASSET INVENTORY

### 4.1 Pools and paths (measured row counts)

| asset | rows | cols | size | window | status |
|---|---:|---:|---:|---|---|
| `phase16/.../pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` | 27,658 | 78 | 5.70 MB | Jan 2026, TRUE UTC | **HEAVILY READ** — the swarm's primary substrate; T1/T2, funnel_jan, scorecard, calibration, w0 all read it |
| `phase18/.../pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` | 27,658 | 12 | 34.13 MB | Jan 2026, M1 bars | READ by w0 (fully consumed into the working set) |
| `phase19/discovery/w0_WORKING_SET.jsonl.gz` | 27,658 | 128 | 10.34 MB | Jan 2026 | **BUILT BY WAVE 0 — read this** |
| `phase19/discovery/w0_R_PATHS.jsonl.gz` | 27,658 | 10 | 23.58 MB | Jan 2026 | bar-level R arrays, built by wave 0 |
| `phase18/.../pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` | 24,239 | 101 | 5.34 MB | Feb 2026, TRUE UTC | **USED-ONCE VAL.** Wave 18 read it pre-outcome and it REJECTED broad V4 (0/20 positive days, precision 0.309 vs 0.606 breakeven). Not virgin. Do not re-spend. |
| `phase18/.../pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz` | 4,263 | 24 | 0.92 MB | Jan 2026 | READ by CQ — the inverted-breaker candidate (+11.9 net R/trade TRAIN and Jan VAL) |
| `phase16/.../pools/CD_REPAIRED_POOL_S0R0_V1.jsonl.gz` | 28,544 | 78 | 5.89 MB | Jan 2026, **UTC+2 (pre-CJ clock)** | superseded by CJ; comparator only |
| `phase16/.../pools/CD_REPAIRED_POOL_S0R1_V1.jsonl.gz` | 28,546 | 78 | 5.89 MB | Jan 2026, UTC+2 | sizing-switch arm, pre-clock |
| `phase16/.../pools/CD_REPAIRED_POOL_S1R0_V1.jsonl.gz` | 28,552 | 78 | 5.89 MB | Jan 2026, UTC+2 | selection-switch arm, pre-clock |
| `phase16/.../pools/CD_REPAIRED_POOL_S1R1_V1.jsonl.gz` | 28,553 | 78 | 5.89 MB | Jan 2026, UTC+2 | joint incumbent, pre-clock |
| `phase19/forensic/walk/WALK_2D_CANDIDATES.jsonl.gz` | 8,448 | 24 | 0.81 MB | 2-day fixture | walk annex |

**The raw ledger is NOT on this machine.** `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl`
(153,425 rows) is referenced by `phase16/receipts/CJ_RECLOCKED_POOL_S0R0_V1.json` at a path under
`research/operations/final_moonshot_..._2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/` that does not
exist in any worktree. **The 125,767 non-scoreable rows are therefore unrecoverable without a re-run.**

### 4.2 The four CD arms vs the one CJ arm — the clock

The `CD_REPAIRED_*` pools are the **pre-re-clock** generation (sealed labels = true UTC + 2h, CJ, 54/54 weekly
opens). `CJ_RECLOCKED_S0R0_POOL_V1` is the same S0R0 arm at true UTC and is the only re-clocked pool.
**Row counts differ (28,544 vs 27,658)** because re-clocking moves candidates across session and day
boundaries. Never pool a CD arm with the CJ arm, and never carry a CD-derived session/hour finding forward —
the authoritative B_TIME map is `phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json` (all 83 cells negative),
which supersedes AW's.

### 4.3 February carries 23 fields January does not

`CP_FEBRUARY_S0R0_POOL_V1` has **101 fields to January's 78**, and every January field is present. The extra 23:

`raw_gross_r`, `raw_net_proxy_r`, `raw_opportunity_close_reason`, `policy_gross_r`, `opportunity_gross_r`,
`opportunity_close_reason`, `terminal_outcome`, `counterfactual_order_close_time_utc`, **`target_first_touch_utc`**,
**`stop_first_touch_utc`**, **`same_bar_ambiguity`**, **`ambiguity_resolution`**, `terminal_r_diagnostic_outcome`,
`terminal_r_diagnostic_gross_r`, `terminal_r_diagnostic_close_reason`, `terminal_r_diagnostic_target_r`,
`path_source`, `path_source_timeframe`, `path_index_source_path`, `path_index_source_sha256`,
`path_index_rows_returned`, `path_row_count`, `ordered_tick_truth_satisfied`.

**February's pool carries first-touch timestamps and same-bar ambiguity resolution INLINE.** January needs the
separate path sidecar to get the same thing. If you need a first-touch or ambiguity method validated, February
is the pool that already answers it — but note February is used-once VAL and its economics are spent.

### 4.4 Receipt directories

| directory | contents | status |
|---|---|---|
| `phase19/receipts/discovery/` | 40 files — the wave-0 working set, helper, README, build receipts, and this dictionary | **the swarm's shared substrate** |
| `phase19/receipts/forensic/t1/` | `T1_SCREENS_V1.json/.md`, `CELL_DECLARATION_V1.md`, 3 working scripts (`t1_screens.py`, `t1_fill_axis.py`, `t1_rcaps_frontier.py`) | READ — copy the scripts, they already stream the pool correctly |
| `phase19/receipts/forensic/t2/` | the six January arms: `T2_ARM_{I..V}_ANALYSIS.json`, `T3_SWAP_ISO_ANALYSIS.json`, `T2_ARMS_V1.md` | READ — these answered "is it defensible", never "where does the money go" |
| `phase19/receipts/forensic/a1_cleanroom/` | 19 files — A1 method-defect adjudication, corrected nulls | READ |
| `phase19/receipts/forensic/a2_verify/` | 40 files — recomputes, reconciliation, family-tension | READ |
| `phase19/receipts/forensic/walk/` | `WALK_2D_ANNEX`, `WALK_2D_CANDIDATES.jsonl.gz` (8,448) | READ |
| `research/operations/wave19_broad_forensic_2026_08_01/` | 8 lanes: `funnel_jan` (12), `funnel_feb` (15), `scorecard` (13), `calibration` (8), `cartographer` (7), `priors` (6), `trades_jan` (6), `trades_feb` (9) | READ — see §5 note on `cartographer/DECISION_CYCLE_MAP.md` |
| `phase19/receipts/march/` (worktree `fa2-integration-20260803`, branch `phase19/march-confirm`) | 13 top-level + `analysis/` (7 arm analyses) + `arm_receipts/` (12 + six `*_LANE` dirs each with `LANE_RUN_RECEIPT.json` + `LANE_TRADE_TABLE.jsonl`) | READ — six March arms; corroborates the 7.3-8.5x spread overcharge independently |
| `phase16/receipts/` | 40 files incl. `CJ_PACKS_{JANUARY,FEBRUARY,APRIL,MAY}_*.json` and 4 `*_LANE` dirs | pack manifests |
| `phase18/receipts/` | 26 files incl. `CANDIDATE_FAMILY_V26/V27.json`, `CP_TRUE_UTC_B_TIME_MAP_V1.json` | the V27 family tip = the multiplicity bill |

### 4.5 What is still VIRGIN — Wave 2's fuel

| window | pack | status |
|---|---|---|
| **January 2026** | `CJ_PACKS_JANUARY_V3.json` | SPENT — the substrate of this whole swarm |
| **February 2026** | `CJ_PACKS_FEBRUARY_V2.json` | **USED ONCE (wave 18) and it REJECTED.** Economics spent. Method-validation use only. |
| **March 2026** | six arms under `phase19/receipts/march/` | READ by the fa2 lane. Note CLAUDE.md's standing "keep March outcome-unread" was **overtaken** — March has been read. |
| **April 2026** | `CJ_PACKS_APRIL_V2.json` | **ECONOMICS UNREAD — VIRGIN.** True-UTC lane pack exists. Wave 2 fuel. |
| **May 2026** | `CJ_PACKS_MAY_V1.json` | **ECONOMICS UNREAD — VIRGIN.** True-UTC lane pack exists. Wave 2 fuel. |

**April and May are the only two windows whose economics have never been read.** Session CS was
commissioned to read them as CQ's two missing gate folds. **Do not spend them in Wave 1.**

---

## 5. THE DECISION PATH — generation to fill, in one page

Ordered stages. `verdict field(s)` are the pool columns that record each stage's outcome, so you can
navigate the funnel without re-reading source. **Survivor counts are measured over this pool** (n=27,658).

| # | stage | source | verdict field(s) | measured |
|---|---|---|---|---|
| 1 | Candidate generation — origin family fires on an M15 bar | `components/broader_origin_generators.py` (`origin_family` :442, geometry :1909, session :1934-1944) | `origin_family`, `entry_price`, `stop_loss`, `take_profit_1`, `decision_time_utc` | 27,658 candidates, 10 families, 24 symbols, 1,969 M15 windows |
| 2 | Geometry contract — target fixed at 2R | `v4_timewarp:88504` (`raw_target_r`), `:88931` (`policy_target_r`) | `take_profit_1`, `policy_target_r`, `raw_target_r` | `take_profit_1` implies **exactly 2.0000R on all 27,658**; `policy_target_r` disagrees on 1,229 (4.44%) |
| 3 | Belief attachment — probability and EV | `components/ultimate_candidate_package.py:1724-1727`, `:2985-2988` | `candidate_probability`, `candidate_ev_r`, `expectancy_r`, `candidate_confidence` | p mean **0.7658** vs measured 0.3468; EV **positive on every row**; confidence a constant 0.55 default |
| 4 | **Broker pretrade cost packet** — the dominant gate | `components/broker_net_cost_engine.py`: spread `:298-306`, total `:700-706`, refusal reasons `:846-928`, status `:842` | `spread_r`, `cost_r`, `commission_r`, `swap_cost_r`, `pretrade_cost_packet_status`, `broker_pretrade_cost_executable` | **20,448 REFUSED (73.93%) / 7,210 PASSED**. Spread limb binds 84.4% of refusals |
| 5 | Fill-quality attachment | `components/poi_execution_lifecycle.py:174-199` (`fill_probability`), `:407`, `:224` (`limit_marketable_at_decision`) | `fill_probability`, `execution_fill_probability`, `limit_fillability_probability`, `limit_marketable_at_decision` | `limit_marketable_at_decision` **85.19% null**; the two executable booleans are `True` on every row |
| 6 | Selector V4 admission | `components/selector_v4.py`: EV limb `:3832`, cost limb `:3843`, sleeve `:3960`/`:4500`, off-session `:2556`/`:4412`, reason `:3592` | `selector_action`, `selector_reason`, `admission_risk_class` | reject **83.22%**; only **21 rows** reach `trade`. 73.61% of rejections are cost-derived |
| 7 | Package authority — sleeve match and admission count | `components/live_decision_packet_v4.py:486`, `moonshot_scheduler_v4:6181` | `matched_sleeve_count`, `effective_admission_count` | matched mean 1.187 (max 5); effective **never exceeds 2** |
| 8 | Scheduler materialization | `v4_timewarp:27855-27862`; window build `:78014` | `scheduler_materialization_status`, `scheduler_selection_disposition` | **4,095 materialized (14.81%)** — and this is exactly where the fill fields get written |
| 9 | Scheduler allocation / veto | `moonshot_scheduler_v4:15525` (displacement), `v4_timewarp:41945-41963` (option status) | `effective_selector_action`, `effective_selector_reason`, `miss_reason` | 3,899 generated-not-selected; **196** preselected-then-rejected-by-finalizer |
| 10 | Risk finalizer | `v4_timewarp:28810` (rank), `:28813` (reason); marketable guard `moonshot_scheduler_v4:13397`, `:18189` | `risk_finalizer_rank`, `risk_finalizer_reason` | rank 1..149; 73.93% `broker_cost_authority_blocked_non_executable`, 14.81% `package_executable_authority_required_not_met` |
| 11 | Order materialization | `v4_timewarp:88003`, `:88298` | `effective_order_type`, `candidate_lifecycle_action` | `limit` 23,106 / `none` **4,552 (16.46% never got an order type)**; `new_position` 4,512 |
| 12 | Fill realism classification | `v4_timewarp:60447-60448` | `fill_realism_class`, `fill_realism_executable`, `entry_fill_executable` | `passive_queue_confirmed` 21,052 / `source_safe_immediate_marketable` 6,606. **Both booleans True on every row — never tested against the path.** |
| 13 | Blocker resolution (post-hoc) | cascade `moonshot_scheduler_v4:14265-14349`; precedence `order_blocker_precedence.py:172-188`; carried `v4_timewarp:13686`, `:15391` | `final_blocker_class`, `miss_reason` | cost_authority 73.93%; `fill_realism` is the **fallthrough default**; co-blockers **not projected** |
| 14 | Counterfactual walk + scoreability | `v4_timewarp:92730`/`:93122` (net proxy), gate `:28130-28146`, status `:28156` | `opportunity_net_proxy_r`, `missed_opportunity_r_scoreability_status` | **153,425 ledger rows -> 27,658 pool rows (18.03%)**, all diagnostic, **zero executed** |
| 15 | Path walk (sidecar, separate asset) | `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1`; derived in `w0_build_working_set_v2.py` | `mfe_r`, `mae_r`, `which_came_first`, `bars_to_*`, `r_at_bar_*` | 120 M1 bars max = **2h hard cap**; first touch target 24.40% / stop 50.60% / **neither 25.01%** |

**A deeper 596-line walkthrough already exists** at
`research/operations/wave19_broad_forensic_2026_08_01/cartographer/DECISION_CYCLE_MAP.md` (launch chain,
`evaluate_candidate_v4` at `v4_timewarp:67389`, `materialize_scheduler_window` at `:78014`,
`allocate_decision_window` at `scheduler:27866`, `finalize_scheduler_risk_admitted_selection` at `:44810`,
`simulate_order` at `:85822`). **This table is the index; that file is the manual.** Read it before
proposing any change to a stage.

### 5.1 Where the funnel actually loses candidates

| after stage | survivors | lost | cumulative survival |
|---|---:|---:|---:|
| generated | 27,658 | — | 100.00% |
| cost packet PASSED | 7,210 | 20,448 | 26.07% |
| scheduler materialized | 4,095 | 3,115 | 14.81% |
| reached `new_position` | 4,512 | — | 16.31% |
| selector said `trade` | 21 | — | 0.08% |
| actually executed | **0** | — | **0.00%** |

`new_position` (4,512) exceeds `scheduler_option_materialized` (4,095), so the two are not nested — the
lifecycle action is written on a different branch from the scheduler status. Do not build a strict funnel
out of these two columns.

---

## 6. PROVENANCE

| receipt | what it holds |
|---|---|
| `w0_DICTIONARY.json` | machine-readable twin of this file: every field's profile, curated meaning, source line, trust class and flags |
| `w0_POOL_PROFILE.json` | per-field dtype / null rate / cardinality / min / max / mean / median / p05 / p95 / top-6 |
| `w0_DICT_ENUMS.json` | full value distributions for all 27 categorical and low-cardinality fields |
| `w0_DICT_COSTGATE.json` | the two-limb cost-gate decomposition (§0.2) |
| `w0_DICT_OVERCHARGE.json` | pass-rate sweep over spread divisors 1x .. infinity (§0.2) |
| `w0_DICT_IDENTITIES.json` | the exact-duplicate verification and the Jan/Feb schema diff |
| `w0_DICT_SRCTRACE.json` | every field's writer/reader sites across all 677 files in `src/` |
| `w0_DICT_ASSETS.json` | measured row counts and byte sizes for every pool and path asset |
| `w0_dictionary_meta.py` | the curated meanings/flags table (editable source of §1) |
| `w0_dictionary_build.py` | this generator |
| `w0_dictionary_trace.py` | the `src/` tracer |

Upstream, not re-derived here: `w0_RESULT.md` (W0-F1..F4), `w0_WORKING_SET_README.md`,
`w0_WORKING_SET_BUILD_V2.json` (31/31 validations).

