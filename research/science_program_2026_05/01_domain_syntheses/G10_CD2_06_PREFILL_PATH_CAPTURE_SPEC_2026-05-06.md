# G10 CD2-06 Prefill Path Capture Spec - 2026-05-06

Lane: `G10`  
Assignment: `CD2-06 - Pre-fill delivery path and no-retrace opportunity map`  
Primary owner: `G10`  
Seed rows: `G10-HYP-PREFILL-003`, `G10-HYP-XDOMAIN-008`, `G6-HYP-002`, `HYP-G4-FILL-QUALITY-009`  
Promotion verdict: `NO_PROMOTION_VERDICT`

## Scope Boundary

This artifact is a G10-owned cross-domain second-pass capture specification. It defines the data contract needed to study setup-decision-to-fill/cancel path behavior, continuation/no-retrace opportunities, and adverse-fill mechanisms. It does not score a live strategy, does not edit master registries, and does not authorize changes to live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.

## Controlling Inputs Read

| Input | Evidence role |
|---|---|
| `research/science_program_2026_05/04_goal_prompts/G10_G10_EXECUTION_RISK_GOAL_PROMPT_2026-05-06.md` | G10 lane scope, required outputs, forbidden surfaces, and `NO_PROMOTION_VERDICT`. |
| `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md` | CD2-06 objective, seed rows, required blocker checks, and stop output. |
| `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md` | Master registry is research-control inventory only; survivor backlog is zero. |
| `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md` | G0 recorded G10/G6/G4 source, label, and sample blockers after wave-2 reconciliation. |
| `research/science_program_2026_05/01_domain_syntheses/G10_EXECUTION_RISK_DOMAIN_SYNTHESIS_2026-05-06.md` | G10 mechanism framing: internal pending, pre-fill timing, slippage/cost, label separation. |
| `research/science_program_2026_05/01_domain_syntheses/G6_MOMENTUM_REVERSION_DOMAIN_SYNTHESIS_2026-05-06.md` | No-retrace rows are lifecycle context only until exact decision entry and ordered path exist. |
| `research/science_program_2026_05/01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_SYNTHESIS_2026-05-06.md` | Fill quality needs source-valid depth/flow, lifecycle truth, and separated broker actual-R labels. |
| `research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md` | Current prefill audit substrate and documented field gaps. |
| `research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md` | Current continuation/no-retrace source blockers. |

## Mechanism To Capture

The primitive is not "enter every missed move." The primitive is whether the path after setup decision but before fill/cancel contains decision-time-observable execution state:

- no-retrace continuation: price reaches target area before retracing to the intended entry;
- adverse fill: price reaches entry, then moves quickly toward stop or through a poor-liquidity state;
- clean fill: entry is touched and the next resolved path favors the intended target before invalidation;
- stale/late fill: path has already delivered the move or changed state before the internal pending route triggers;
- lifecycle cancel/expiry: the pending intent terminates before a broker-realized fill.

All five are lifecycle/path labels, not broker actual-R labels.

## Required Row Families

CD2-06 needs four row families joined by stable keys. If any family is missing, the row can remain in the audit, but the missing source must be explicit.

| Row family | Current local anchor | Purpose | Feature or label lane |
|---|---|---|---|
| Decision packet | `shadow_logs/strategy_follow_candidates.jsonl`, `shadow_logs/prefill_delivery_path.jsonl` | Freeze setup geometry and intended route as of decision/arming time. | Feature/source lane only. |
| Ordered path packet | `shadow_logs/candidate_ltf_path_order.jsonl`, future tick path summary | Prove entry/TP/SL ordering from decision/arm to fill/cancel. | Post-decision label lane; not a decision feature. |
| Pending lifecycle packet | `shadow_logs/pending_limit_lifecycle.jsonl`, `shadow_logs/pending_limit_lifecycle_audit.jsonl` | Separate internal pending state, cancel/expiry, trigger, market order attempt, and broker fill state. | Lifecycle label lane. |
| Execution/friction packet | `shadow_logs/slippage.jsonl`, `shadow_logs/broker_actual_r_audit.jsonl`, future source-valid G4 depth/flow rows | Study adverse fills and clean fills only after fill/slippage/depth evidence exists. | Slippage/broker actual-R/depth context lanes, kept separate. |

## Stable Join Keys

Every CD2-06 row must preserve these fields, even when a value is `SOURCE_NOT_CAPTURED`:

| Field | Contract |
|---|---|
| `candidate_id` | Primary forward-shadow join key. Must not be derived from outcome. |
| `structural_setup_id` | Stable setup/POI identifier. Use `candidate_id` only as fallback and mark fallback. |
| `trade_id` | Broker/order lifecycle join key when available. Missing trade IDs are allowed but block broker-fill claims. |
| `symbol`, `broker_symbol`, `source_symbol` | All three symbols remain separate to prevent CFD/futures/source-transfer confusion. |
| `decision_time_utc` | Setup decision close timestamp. |
| `entry_arming_time_utc` or `pending_created_time_utc` | Internal pending creation/arming timestamp. |
| `asof_cutoff_utc` | Last observation allowed in the decision packet. |
| `source_file`, `source_hash` | Source provenance. Missing hash blocks validation-safe claims. |

## Decision Packet Required Fields

These fields are allowed as decision-time features for `G10-HYP-PREFILL-003`, `G10-HYP-XDOMAIN-008`, and G6/G4 joins:

| Field group | Required fields | Current status expectation |
|---|---|---|
| Setup geometry | `side`, `entry_price`, `stop_loss`, `take_profit_1`, `target_area_model`, `stop_model` | Entry/SL/TP may be available through `strategy_follow_candidates`, but must be copied or explicitly joined into the CD2-06 row before analysis. |
| POI geometry | `original_poi_type`, `original_poi_bounds`, `h1_poi_price_level`, `zone`, `framework` | Forward prefill rows currently capture POI bounds; historical path replay did not. |
| Pending route | `pending_order_mode`, `broker_pending_order_created`, `pending_ticket`, `mt5_order_ticket`, `native_pending_order_type` | Must distinguish internal candle-polled intent from native broker pending exposure. |
| Context | `session`, `kill_zone`, `regime`, `spread_at_decision_or_arm`, `source_symbol`, `source_hash` | Missing source or spread fields remain audit blockers. |
| Neighbor bridge | `g6_setup_asof_utc`, `g10_lifecycle_state_asof_utc`, `g4_source_status` | Only context bridge fields; no outcome values. |

## Ordered Path Packet Required Fields

The path packet must be ordered from `entry_arming_time_utc` through the earliest terminal state: entry touch, TP-area before entry, SL-area before entry, cancel, expiry, or unresolved as-of cutoff.

| Field | Required detail |
|---|---|
| `path_timeframe` | Prefer `tick`, then `M1`, then `M5`; `M15` is diagnostic only and cannot resolve same-bar ordering. |
| `path_source_start_utc`, `path_source_end_utc` | Bound the exact post-decision observation window. |
| `pre_fill_candles` | Ordered candle array with at least time, OHLC, spread if available, and source row identity. |
| `pre_fill_ticks_summary` | Required when a candle contains entry plus TP/SL or when adverse-fill timing is under one bar. |
| `entry_first_touch_utc`, `tp1_first_touch_utc`, `sl_first_touch_utc` | First-touch timestamps from ordered path only. |
| `terminal_order_ambiguity` | Boolean plus reason code. Ambiguous rows must not be guessed. |
| `tick_order_claim_status` | `TICK_ORDER_CONFIRMED`, `NO_TICK_ORDER_CLAIM_M1_ONLY`, or `NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY`. |

## Pending Lifecycle Packet Required Fields

Lifecycle state is separate from path touch. A path touch is not a broker fill.

| Field | Required detail |
|---|---|
| `pending_created_time_utc` | Exact internal arming time. |
| `pending_order_mode` | Expected current value is internal intent unless native broker pending exists and is explicitly marked. |
| `broker_pending_order_created` | Boolean; false means no native broker exposure. |
| `intent_after_check` | One of the pending lifecycle states, such as still pending, cancelled, expired, retry, or filled. |
| `trigger_condition_met` | Whether the internal pending route saw its trigger. |
| `tick_available` | Whether the trigger could be checked on a current tick. |
| `order_send_attempted`, `order_send_success` | Market-order translation evidence after internal trigger. |
| `fill_time_utc`, `broker_fill_state`, `mt5_order_ticket` | Broker-facing fill evidence. Missing values block fill-quality and broker actual-R claims. |
| `cancel_reason`, `expiry_time_utc` | Terminal no-fill state. |

## Execution And G4 Fill-Quality Packet

`HYP-G4-FILL-QUALITY-009` can only be studied after the execution/friction packet is joined without mixing label families.

| Field group | Required fields |
|---|---|
| Spread/slippage | `pre_touch_spread`, `spread_at_request`, `requested_price`, `fill_price`, `slippage_price`, `slippage_directional`, `slippage_pips`. |
| Depth/flow source status | `pre_touch_depth10`, `pre_touch_delta`, `queue_pull_or_depth_thinness_state`, plus source contract/proxy status. |
| Broker accounting | `account_history_realized_flag`, `broker_actual_r`, `commission`, `swap`, `close_fill_utc`, `exit_accounting_status`. |
| Label guard | `fill_no_fill_label`, `synthetic_path_r_status`, `broker_actual_r_claim_allowed`, `truth_lane`. |

## Label Separation Rules

| Label family | Allowed use | Prohibited use |
|---|---|---|
| `lifecycle_no_fill` | Fill/no-fill, cancel, expiry, trigger, order-send state. | Cannot be converted to R. |
| `synthetic_path_r` | Research-only path comparator when exact ordered path exists. | Cannot overwrite broker actual-R or validate execution quality. |
| `broker_actual_r` | Only account-history realized rows with cost accounting. | Cannot be inferred from candidate or path rows. |
| `context_only` / `observation_only` | G6/G4/G10 conditioning context. | Cannot become a live filter or selector. |

## Same-Bar Ambiguity Classification

Rows must carry one of these states:

| State | Meaning | Scoreability |
|---|---|---|
| `TICK_ORDER_CONFIRMED` | Ordered tick path proves entry/TP/SL sequence. | Eligible for future frozen path scoring if other fields pass. |
| `M1_ORDER_CONFIRMED` | M1 sequence proves ordering across separate M1 bars. | Eligible for lifecycle/path classification; tick still required for intra-M1 claims. |
| `SAME_M1_AMBIGUOUS_ENTRY_TP_SL` | Entry plus TP/SL occur inside one M1 bar. | Excluded from R scoring unless tick order is available. |
| `M15_PATH_AMBIGUOUS_TP1_AND_SL` | Only M15 OHLC indicates both target and stop. | Diagnostic only. |
| `NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL` | Target area reached before limit touch. | Lifecycle no-fill/no-retrace label only. |
| `SOURCE_BLOCKED_NO_ORDERED_PATH` | No lower-timeframe or tick sequence available. | Blocked. |

## Study Eligibility Gates

| Study | Minimum CD2-06 fields before analysis | Current promotion verdict |
|---|---|---|
| `G10-HYP-PREFILL-003` | Exact POI bounds, entry/SL/TP, ordered M1/tick path, pending lifecycle final state, no-leak source hash. | `NO_PROMOTION_VERDICT` |
| `G10-HYP-XDOMAIN-008` | G6 setup fields and G10 lifecycle state frozen before outcome, shared setup key or explicit match confidence. | `NO_PROMOTION_VERDICT` |
| `G6-HYP-002` | Exact decision entry price, target/stop models, ordered post-decision M1/tick path, duplicate-aware countability. | `NO_PROMOTION_VERDICT` |
| `HYP-G4-FILL-QUALITY-009` | Fill/no-fill truth, pre-touch spread/depth/flow status, slippage/fill evidence, broker actual-R only for filled account-history rows. | `NO_PROMOTION_VERDICT` |

## Stop Conditions

CD2-06 remains a capture/audit lane and must stop before:

- changing `m15_choch_exists`, pending-limit behavior, order routing, risk sizing, selector logic, prompt wording, or safety gates;
- scoring no-retrace as a live strategy;
- treating OHLC touches as broker fills;
- joining fill/no-fill lifecycle rows into broker actual-R;
- using post-decision path labels as decision-time features;
- marking any source contract validation-safe.

Final artifact verdict: `NO_PROMOTION_VERDICT`.
