# Live Shadow Capture Gap Audit - 2026-05-04

Status: active gap audit
Promotion posture: `NO_PROMOTION_VERDICT`
As-of: 2026-05-04 08:30 UTC M15 close

This audit separates structural JSON integrity from semantic capture coverage. `scripts/verify_shadow_log_integrity.py` reports `OK_WITH_DOCUMENTED_WAITING_LANES`, but several live-shadow lanes still do not capture enough information to answer the owner's follow-data questions without manual joins, assumptions, or missing metadata.

## Current Counts

- `strategy_follow_evaluations.jsonl`: 60 rows.
- `strategy_follow_candidates.jsonl`: 8 rows.
- `candidate_path_follow.jsonl`: 33 rows.
- `live_mechanical_strategy_shadow_outcomes.jsonl`: 528 rows.
- `pending_limit_lifecycle.jsonl`: 17 rows.
- `v2b_forward_pairs.jsonl`: 8 rows.
- `prefill_delivery_path.jsonl`: 8 rows.
- `fvg_ob_confluence.jsonl`: 8 rows.
- `context_control_ledger.jsonl`: 8 rows.
- `shadow_observer_status.jsonl`: 70 rows.
- `shadow_observer_tick_enrichment.jsonl`: 7 rows.
- `databento_live_confluence.jsonl`: missing / 0 rows.
- `session_volatility_log.csv`: missing / 0 rows.
- `sweep_divergence_log.csv`: missing / 0 rows.

## Critical Gaps

### 1. Exact V2/V3 structural and reentry systems are still not live-scorable

Latest mechanical shadow status across 8 candidates:

- `MISSING_REQUIRED_LIVE_METADATA`: 64 latest rows.
- Affected strategy IDs: `V2_STRUCT_SWING_PROTECTED`, `V2_STRUCT_FVG_MID_EDGE`, `V2_STRUCT_COMPOSITE_ANY`, `V3_FVG_ONLY_RESCUE_RISK_BANK`, `V3_FVG_THEN_OB_TAIL_RISK_BANK`, `V3_OB_LOCK_PULLBACK_RISK_BANK`, `V3_OB_LOCK_COST_AWARE_MIN_R`, and `FVG_OB_CONFLUENCE_OB_AFTER_FVG`.

The current rows do not preserve standalone FVG entry geometry, FVG lock state, swing-protected lock level, structural-lock event time/price, reentry state, or cost-aware min-R fields. This means the rows tell us the shared candidate path but not what those exact systems would have done.

Required fix: capture decision-time structural selector metadata from the MSO and path-scaling rules for every candidate, then score these systems from their own live state instead of marking them as missing.

### 2. Pending-limit lifecycle rows cannot be safely joined to candidates

`pending_limit_lifecycle.jsonl` rows currently have `candidate_id=null` and `decision_time_utc=null`. The `trade_id` is also minute-based and collides across symbols: `lim_2026-05-04_0715` exists for both XAUUSD and NAS100.

This makes joins fragile and can overwrite or confuse per-trade summaries if a script keys only by `trade_id`.

Required fix: propagate `candidate_id`, `decision_time_utc`, and source metadata into `PendingLimitIntent` / lifecycle telemetry, and make the lifecycle join key symbol-aware or globally unique. Backfill today's lifecycle rows from candidate records where the mapping is unambiguous.

### 3. V2b, pre-fill path, and FVG/OB confluence ledgers are decision-time placeholders only

`v2b_forward_pairs.jsonl`, `prefill_delivery_path.jsonl`, and `fvg_ob_confluence.jsonl` have 8 rows each, but their outcome fields remain unresolved placeholders. The computed path outcomes exist in `live_mechanical_strategy_shadow_outcomes.jsonl`; they are not appended back as resolved rows in the specific research ledgers.

Required fix: add append-only resolver rows for these ledgers, with no-leak status, as-of candle, candidate path label, fill/no-fill state, and path metrics.

### 4. Missed-opportunity monitoring is not a first-class strategy lane

XAUUSD 07:15 SHORT and NAS100 07:15 LONG both reached the TP1 area without the limit filling. This is logged as `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`, but there is no separate market-entry/proximity-entry/missed-opportunity comparator strategy.

Required fix: add a shadow-only missed-opportunity comparator that records market-at-close, proximity-entry, and limit-entry outcomes separately. This is observation-only and must not change execution behavior without approval.

### 5. Lower-timeframe path ordering is not joined into live candidate outcomes

Current candidate path follow uses post-decision candle high/low/close and labels same-bar ambiguity as unresolved in V2b rows. It cannot fully answer intra-candle ordering, touch-before-reversal, or TP/SL ordering questions.

Required fix: join M1 and/or tick path slices for each candidate window and write lower-timeframe path-order rows for candidate, V2b, pre-fill, and V3 scorers.

## High-Priority Gaps

### 6. Databento live confluence is not being utilized by an event-trigger policy

All 8 candidate rows show Databento `DISABLED_BY_ENV` / `NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE`; `shadow_logs/databento_live_confluence.jsonl` is missing. Sierra features are attached, but there is no cost-capped decision layer that says "this candidate needs a Databento live pull" versus "do not spend."

Required fix: implement a trigger policy that uses Databento only for registered event types and symbols, especially NAS100/NQ orderflow diagnostics, with explicit spend accounting and no every-candle polling.

### 7. XAGUSD/SI Sierra depth is captured but still source-definition blocked

The live XAGUSD candidate rows attach Sierra `SIM26-COMEX` depth features with sample counts, but earlier Sierra/Databento parity work marks SI as source/depth-definition blocked. The row captures data, but the downstream interpretation should carry that source-status warning.

Required fix: add `source_status` / `parity_status` into Sierra confluence rows so XAGUSD/SI features cannot be mistaken for validated Databento-equivalent fields.

### 8. Shadow observer status rows are semantically weak

The latest observer status rows for EURUSD, GER40, and UK100 use `reason=already_emitted_for_candle` but do not consistently carry canonical status fields such as `latest_closed_m15_utc`, row counters, or explicit zero AI/Databento/order call counters at the top level.

Required fix: normalize `shadow_observer_status_v1` so every heartbeat/status row has the same top-level operational fields.

### 9. Session volatility and US30 sweep divergence logs are absent

Scripts exist (`scripts/session_volatility_monitor.py`, `scripts/sweep_divergence_monitor.py`), but `shadow_logs/session_volatility_log.csv` and `shadow_logs/sweep_divergence_log.csv` are missing / 0 rows. The coverage audit classifies this as `SCRIPT_OUTPUT_WAITING_OR_STALE_CHECK_REQUIRED`.

Required fix: verify watchdog/manual cadence and create fresh rows or explicit no-event rows, so missing files are not confused with no signal.

### 10. Candidate snapshot rows remain permanently unresolved

`strategy_follow_candidates.jsonl` intentionally records decision-time snapshots, but every strategy snapshot still says `UNRESOLVED_REQUIRES_FORWARD_JOIN`. The resolved information lives in separate logs, requiring manual joins.

Required fix: add a latest-state rollup log or report keyed by candidate and strategy, so monitoring can read one append-only summary without reconstructing joins manually.

## Medium-Priority / Blocked Gaps

### 11. Broker actual-R / account truth is still not automated enough

No open positions exist now, so BE/partial/time-in-trade rows are correctly event-waiting. But account-history reconciliation is still a separate verifier requirement, and stale local PnL artifacts remain known-risk evidence. Dollar/R claims should still use account-history truth over local shadow PnL.

Required fix: automate read-only MT5 account-history reconciliation and tag `ACCOUNT_HISTORY_REALIZED`, `LIVE_R_ARTIFACT`, and `RESEARCH_MEASURED` separately.

### 12. GBPJPY has no registered direct Sierra/Databento proxy

GBPJPY candidate/orderflow confluence cannot be captured directly from Sierra/Databento without a separate 6B/6J cross-proxy design. This is not a live-row bug, but it is still a forward-context gap.

Required fix: design and validate a GBPJPY proxy plan before using futures confluence on GBPJPY rows.

### 13. ML/K55 shadow predictions are absent

`shadow_logs/ml_shadow_predictions.jsonl` is missing. Existing audit status is `APPROVAL_OR_TARGET_REFRESH_BLOCKED`. This is not running today.

Required fix: if kept in the follow-data program, build a no-execution shadow scaffold after target refresh and owner approval.

### 14. ES/MES, CL, ZN, VIX/VXM, options/gamma, and older-data source items remain source/pre-registration blocked

These are not live candidate bugs today, but they remain follow-up gaps from the broader research queue. They require pre-registration, legal/source/cadence definitions, or source access before useful live capture can be claimed.

## Current Candidate Interpretation

- XAUUSD 07:15 SHORT `LIMIT_PLACED`: no fill, TP1 area reached without entry touch.
- NAS100 07:15 LONG `LIMIT_PLACED`: no fill, TP1 area reached without entry touch.
- XAGUSD 07:15, 07:30, 07:45, 08:00, 08:15 SHORT: L2-rejected on `m15_choch_exists`, entry touched, no TP1/SL by 08:30.
- XAGUSD 08:30 SHORT: L2-rejected on `m15_choch_exists`, no entry touch yet by 08:30.

## Boundary

Fixing additive shadow capture gaps is operationally safe when it does not change trading decisions, prompts, risk, execution, safety gates, canary behavior, or paid-data spend. Behavior-changing logic and paid Databento activation still need explicit controls.
