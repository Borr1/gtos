# G10 CD2-06 Prefill Path Missing-Field Audit - 2026-05-06

Lane: `G10`  
Assignment: `CD2-06 - Pre-fill delivery path and no-retrace opportunity map`  
Primary owner: `G10`  
Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective Restated

Audit the actual current field coverage for CD2-06 after reading HEAD `48389494`, the G10 goal prompt, G0 second-pass assignment, master registries, G0 wave-2 reconciliation, and the relevant G10/G6/G4 artifacts. The audit determines what is captured now and what is still missing before setup-decision-to-fill/cancel path rows can study no-retrace and adverse-fill mechanisms around `G10-HYP-PREFILL-003`, `G10-HYP-XDOMAIN-008`, `G6-HYP-002`, and `HYP-G4-FILL-QUALITY-009`.

This is a missing-field audit only. It does not score a live strategy, edit master registries, or change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.

## Current Evidence Summary

| Evidence source | Current count or status | Audit interpretation |
|---|---:|---|
| `shadow_logs/prefill_delivery_path.jsonl` | `76` rows | Core forward prefill decision packets exist. |
| `shadow_logs/prefill_delivery_path_audit.jsonl` | `1073` rows | Latest-by-candidate audit shows all 76 current prefill rows are complete with documented limitations. |
| `shadow_logs/prefill_delivery_path_resolutions.jsonl` | `1648` rows | Path resolutions exist, but are labels, not decision features. |
| `shadow_logs/candidate_ltf_path_order.jsonl` | `1611` rows | Lower-timeframe path ordering exists for many candidates; some remain source-blocked or ambiguous. |
| `shadow_logs/pending_limit_lifecycle.jsonl` | `141` rows | Pending lifecycle rows exist, but current row coverage is incomplete for broker-native and order-send state. |
| `shadow_logs/pending_limit_lifecycle_audit.jsonl` | `45` rows | `39/45` audited rows are action-required because lifecycle groups are missing. |
| `shadow_logs/continuation_no_retrace_candidates.jsonl` | `22` rows | Continuation/no-retrace candidates exist, but exact decision entry price and ordered post-entry path are absent. |
| `research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md` | `76` resolved pairs, `8` duplicate-aware R pairs, `0` broker actual-R pairs | Current V2b/pre-fill labels are primarily synthetic path context, not broker actual-R. |
| `research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md` | `3` account-history-realized rows | Broker actual-R remains too sparse for execution/fill-quality claims. |
| `research/operations/COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-05.md` | `3` entry slippage rows, `0` close-side rows | Fill quality cannot yet include complete cost/exit accounting. |

## Current Prefill Decision Packet Coverage

Latest inspected current prefill rows: `76`.

| Field | Present | Missing | CD2-06 status |
|---|---:|---:|---|
| `candidate_id` | `76/76` | `0/76` | Captured. |
| `symbol` | `76/76` | `0/76` | Captured. |
| `decision_time_utc` | `76/76` | `0/76` | Captured. |
| `asof_cutoff_utc` | `76/76` | `0/76` | Captured. |
| `structural_setup_id` | `76/76` | `0/76` | Captured, currently candidate-derived. |
| `entry_arming_time_utc` | `76/76` | `0/76` | Captured. |
| `original_poi_bounds` | `76/76` | `0/76` | Captured in forward rows. |
| `original_poi_bounds.poi_price_level` | `76/76` | `0/76` | Captured as POI price level. |
| `fvg_ob_swing_state_at_arm` | `76/76` | `0/76` | Captured. |
| `cancel_expiry_abort_reason` | `76/76` | `0/76` | Captured, but this is terminal/lifecycle context, not a decision feature. |
| `source_symbol` | `0/76` | `76/76` | Missing. Blocks source-transfer claims. |
| `source_hash` | `0/76` | `76/76` | Missing. Blocks validation-safe provenance. |
| `trade_id` | `6/76` | `70/76` | Mostly missing. Blocks broker-fill joins for most rows. |
| `pre_fill_candles` | `0/76` | `76/76` | Missing. Blocks exact candle-sequence analysis inside the prefill row. |
| `pre_fill_ticks_summary` | `0/76` | `76/76` | Missing. Blocks tick-order claims and adverse-fill microtiming. |
| `reversal_leg_timing` | `0/76` | `76/76` | Correctly absent from decision packet; should live in resolution labels only. |
| `fill_happened` | `0/76` | `76/76` | Correctly absent from decision packet; should live in lifecycle/resolution labels only. |
| `fill_delay_seconds` | `0/76` | `76/76` | Correctly absent from decision packet; should be derived after path/lifecycle resolution. |

## Strategy-Follow Join Coverage

The same `76` current prefill rows join by `candidate_id` to `shadow_logs/strategy_follow_candidates.jsonl`.

| Joined field | Present through strategy-follow join | CD2-06 status |
|---|---:|---|
| `trade_parameters.entry_price` | `76/76` | Available by join, but should be copied into a CD2-06 decision packet or referenced through an explicit source pointer before analysis. |
| `trade_parameters.stop_loss` | `76/76` | Available by join. |
| `trade_parameters.take_profit_1` | `76/76` | Available by join. |
| Pending/native broker mode fields | `0/76` | Not currently available in joined strategy-follow rows. |

Interpretation: exact entry/SL/TP is available for current prefill rows by join, but the CD2-06 packet itself should preserve these fields or preserve a deterministic join reference. The missing pending/native broker mode fields keep internal-vs-native exposure unresolved for these rows.

## Latest Prefill Audit State

Latest-by-candidate audit rows: `76`.

| Audit field | Counts | CD2-06 interpretation |
|---|---|---|
| `prefill_source_capture_status` | `PREFILL_DECISION_CORE_SOURCE_CAPTURED=76` | Core decision packet exists. |
| `derived_prefill_path_status` | `DERIVED_FROM_CANDIDATE_PATH_ASOF=52`, `DERIVED_FROM_LTF_PATH_ORDER_ASOF=24` | Path labels exist, but only 24 current rows are directly derived from lower-timeframe path-order rows. |
| `duplicate_aware_counting_status` | `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY=12`, `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE=63`, `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP=1` | Current sample is heavily duplicate-concentrated. |
| `path_outcome_status` | `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH=62`, `ENTRY_TOUCHED_THEN_TP1=5`, `ENTRY_TOUCHED_THEN_SL=4`, `ENTRY_TOUCHED_UNRESOLVED=3`, `M15_PATH_AMBIGUOUS_TP1_AND_SL=2` | No-retrace context is visible, but not promotion- or R-scoreable. |
| `decision_prefill_no_leak_status` | `NO_POST_OUTCOME_STATE_IN_PREFILL_DECISION_ROW=76` | Current prefill decision rows pass the decision/no-leak split. |

Documented limitations on all current rows:

- `EXACT_PREFILL_CANDLE_SEQUENCE_SOURCE_NOT_CAPTURED=76`
- `EXACT_PREFILL_TICK_SUMMARY_SOURCE_NOT_CAPTURED=76`
- `PREFILL_SOURCE_HASH_NOT_CAPTURED=76`
- `PREFILL_SOURCE_SYMBOL_NOT_CAPTURED=76`
- `POST_LOCK_REENTRY_ELIGIBILITY_SOURCE_NOT_CAPTURED=76`
- `COST_AWARE_MIN_R_SOURCE_NOT_CAPTURED=76`
- `PREFILL_DELIVERY_REVERSAL_SCORER_NOT_IMPLEMENTED=76`
- `PREFILL_TRADE_ID_NOT_CAPTURED=70`

## Pending Lifecycle Coverage

Current `shadow_logs/pending_limit_lifecycle.jsonl` rows: `141`.

| Field | Present | Missing | CD2-06 status |
|---|---:|---:|---|
| `trade_id` | `141/141` | `0/141` | Captured. |
| `pending_created_time_utc` | `141/141` | `0/141` | Captured. |
| `entry_price`, `stop_loss`, `take_profit_1` | `141/141` | `0/141` | Captured. |
| `fill_no_fill_label` | `141/141` | `0/141` | Captured as lifecycle label. |
| `candidate_id` | `79/141` | `62/141` | Partially missing. Blocks candidate-level joins for older rows. |
| `decision_time_utc` | `79/141` | `62/141` | Partially missing. |
| `checked_candle_time_utc` | `139/141` | `2/141` | Mostly captured. |
| `spread` | `2/141` | `139/141` | Mostly missing. Blocks fill-quality friction study. |
| `tick_bid`, `tick_ask` | `2/141` | `139/141` | Mostly missing. Blocks tick-level trigger/fill reconstruction. |
| `pending_order_mode` | `0/141` | `141/141` | Missing in current rows, despite logger schema support. Blocks internal-vs-native audit from current data. |
| `broker_pending_order_created` | `0/141` | `141/141` | Missing in current rows. |
| `mt5_order_ticket`, `native_pending_order_type` | `0/141` | `141/141` | Missing in current rows. |
| `fill_time_utc`, `slippage_price` | `0/141` | `141/141` | Missing. Blocks broker-fill timing and slippage attribution. |
| `actual_r`, `synthetic_path_r` | `0/141` | `141/141` | Correctly absent from lifecycle rows; R labels must remain separate. |
| `order_send_attempted`, `order_send_success` | `0/141` | `141/141` | Missing. Blocks internal-trigger-to-market-order path study. |

The current pending lifecycle audit has `39/45` rows in `PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED`, mostly because lifecycle groups are missing. Only `6/45` are complete with documented limitations.

## Continuation/No-Retrace Coverage

Current continuation/no-retrace candidate rows: `22`.

| Field or state | Current status |
|---|---|
| Candidate rows | `22/22` have `candidate_id`, `symbol`, and `decision_time_utc`. |
| Exact decision entry price | `0/22` captured as `entry_price` or `decision_entry_price`. |
| Candidate entry/target/stop model fields | `0/22` captured under direct field names. |
| Later path outcomes | `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH=19`, `ENTRY_TOUCHED_UNRESOLVED=3`. |
| Aggregate counting | `COUNTABLE_PRIMARY_ONLY=2`, `EXCLUDED_DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE=19`, `EXCLUDED_BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP=1`. |
| Synthetic R | `NOT_COMPUTED_SOURCE_BLOCKED=22`. |
| Tick-order claim | `NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY=22`. |
| Source blockers | `EXACT_DECISION_ENTRY_PRICE_NOT_CAPTURED=22`, `ORDERED_POST_ENTRY_M1_OR_TICK_PATH_NOT_CAPTURED=22`. |

Interpretation: G6-HYP-002 remains a lifecycle/no-retrace opportunity map only. It cannot be R-scored because exact executable decision price and ordered post-decision M1/tick path are missing for all current continuation/no-retrace rows.

## Lower-Timeframe And Ambiguity Coverage

Current `shadow_logs/candidate_ltf_path_order.jsonl` rows: `1611`.

| Field or state | Counts | CD2-06 interpretation |
|---|---|---|
| `ltf_status` | `M1_PATH_RECOVERED=1498`, `SOURCE_BLOCKED=113` | M1 path recovery exists broadly, but source-blocked rows remain. |
| `same_m1_ambiguity` | `True=70`, `False=1541` | Some rows need tick data before ordering claims. |
| `terminal_order_ambiguity` | `True=10`, `False=1070`, blank/none=`531` | Ambiguity must be classified, not guessed. |
| Top terminal outcome | `NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH=865` | Strong lifecycle no-fill/no-retrace context, not a fill or R label. |

## G4 Fill-Quality Coverage

`HYP-G4-FILL-QUALITY-009` remains source- and sample-blocked for execution-quality claims.

| Requirement | Current state |
|---|---|
| Fill/no-fill lifecycle truth | Partial: pending lifecycle and candidate path labels exist, but lifecycle groups are missing for many audited rows. |
| Pre-touch spread/depth/flow | Mostly missing from G10 rows; current G4 rows require source-valid depth/flow before use. |
| Entry slippage | `3` rows in `shadow_logs/slippage.jsonl` and cost coverage report. |
| Close-side slippage/cost | `0` rows in cost coverage report. |
| Broker actual-R | LTO015 audited `3` account-history-realized rows; current evidence is too sparse for fill-quality claims. |
| Synthetic path versus broker actual-R split | Preserved by current reports; must remain separated. |

## Required Field Audit By Seed Hypothesis

| Seed row | Required before study | Current blocker |
|---|---|---|
| `G10-HYP-PREFILL-003` | Exact POI bounds, entry/SL/TP, ordered path, pending lifecycle final state, source hash, duplicate policy. | POI bounds and entry/SL/TP are available, but source hash, source symbol, prefill candle/tick sequence, pending/native state, and many trade IDs are missing. |
| `G10-HYP-XDOMAIN-008` | G6 setup fields and G10 lifecycle state frozen before outcome, shared setup key or match confidence. | G10 prefill rows exist, but exact G6-compatible no-retrace entry/path fields are missing and G9 remains outside this CD2-06 scope. |
| `G6-HYP-002` | Exact decision entry price, target/stop models, ordered post-decision M1/tick path, duplicate-aware countability. | All `22/22` current continuation/no-retrace rows are source-blocked for exact entry and ordered post-entry path; only `2/22` are primary countable. |
| `HYP-G4-FILL-QUALITY-009` | Fill/no-fill truth, pre-touch spread/depth/flow, slippage/fill evidence, broker actual-R for filled rows. | Lifecycle truth is partial, depth/flow is source-status only, entry slippage has only `3` rows, close-side rows are `0`, and broker actual-R is sparse. |

## Missing-Field Priority Ledger

| Priority | Missing or weak field | Why it matters | Required resolution |
|---:|---|---|---|
| P0 | `source_hash` and `source_symbol` on prefill rows | Without provenance, source-transfer and validation-safe joins are blocked. | Capture file/source identity and hash when writing prefill row. |
| P0 | Exact `entry_price`, `stop_loss`, `take_profit_1` inside CD2-06 packet or deterministic join pointer | G6/G10/G4 cannot study no-retrace or adverse fill without intended price geometry. | Copy from strategy-follow decision packet or record source pointer. |
| P0 | `pre_fill_candles` ordered sequence | Needed to reconstruct decision-to-fill/cancel path and no-retrace ordering. | Store compact ordered M1/M5 sequence or source pointer with row count and window. |
| P0 | `pre_fill_ticks_summary` or tick-order proof for ambiguous rows | Same-bar entry/TP/SL cannot be guessed. | Store tick first-touch ordering or explicit `NO_TICK_ORDER_CLAIM_*`. |
| P0 | Pending/native broker state fields | CD2-06 must separate internal pending from native broker exposure. | Ensure `pending_order_mode`, `broker_pending_order_created`, ticket/type, and order-send fields are present in prospective lifecycle rows. |
| P1 | `trade_id` on prefill rows | Broker fill and actual-R joins need stable order/trade identity. | Capture trade ID when known; otherwise explicit `TRADE_ID_NOT_YET_CREATED`. |
| P1 | Spread/tick at arm and trigger | Adverse-fill and fill-quality mechanisms depend on friction at decision/trigger. | Capture spread, bid/ask, and tick availability at arm/trigger. |
| P1 | Order-send attempt/success and fill timestamp | Internal trigger is not a broker fill until order-send/fill evidence exists. | Preserve order-send and fill result fields in lifecycle rows. |
| P1 | Pre-touch depth/flow source status | G4 fill-quality hypotheses need source-valid depth/flow, not proxy assumptions. | Join Sierra/Databento status and extracted fields only under source contracts. |
| P2 | Close-side cost and broker actual-R sample | Fill quality cannot be promoted without realized cost accounting. | Continue broker/account-history audit; no CD2-06 scoring until sample floors pass. |

## Non-Claims

- `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH` is a lifecycle/path label, not a trade result.
- An OHLC entry touch is not a broker-confirmed fill.
- Current no-retrace rows are not R-scoreable.
- Current fill-quality rows are not execution-policy evidence.
- CD2-06 does not authorize `m15_choch_exists` changes, native pending order activation, risk changes, selector changes, orderflow vetoes, or live execution changes.

Final audit verdict: `NO_PROMOTION_VERDICT`.
