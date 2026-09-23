# Live Shadow Gap Closure Plan - 2026-05-04

Status: superseded by final closure artifact
Owner request: fix every known live-shadow capture gap, backfill the missed live-session data where recoverable, and keep the plan durable outside chat memory.
Source audit: `research/program_control/LIVE_SHADOW_CAPTURE_GAP_AUDIT_2026-05-04.md`
Final closure artifact: `research/program_control/LIVE_SHADOW_GAP_CLOSURE_FINAL_2026-05-04.md`
Boundary: additive shadow capture only. No live trade-decision changes, prompt changes, risk changes, execution-behavior changes, canary/API calls, or paid Databento pulls without explicit controls.

## Operating Rules

1. Every fix must write append-only evidence. Do not overwrite useful live-session data from another source, day, session, or instrument.
2. Every log row must be joinable by `candidate_id`, `symbol`, `source_symbol`, `decision_time_utc`, and an append-time `created_at_utc` or `backfilled_at_utc`.
3. Backfill must be honest:
   - `RECOVERED_EXACT` means the missing value was reconstructed from captured source data.
   - `RECOVERED_DERIVED` means the value was derived from raw live market data after the fact without future leakage beyond the row's declared `asof`.
   - `SOURCE_NOT_CAPTURED` means the original value was not present in any captured source and must not be fabricated.
   - `SOURCE_BLOCKED` means the feature requires a source/proxy definition, owner approval, credentials, or paid-data trigger before it can be emitted.
4. Every data fetch or shadow computation must tag whether it made `ai_calls`, `canary_calls`, `order_calls`, and `paid_data_calls`. Expected value for this closure pass is zero.
5. Every candidate must remain independently reviewable without the AI API response being available. AI output can seed the candidate snapshot, but follow-data rows must be keyed and evaluated by deterministic logs.
6. Staleness must be checked at the log level and at the candidate level. A structurally valid file is not enough if the latest candidate has no fresh follow-up rows.
7. Duplicate protection must be explicit. Any new append-only log must have a deterministic idempotency key and the verifier must check for duplicates.
8. The live monitoring loop must continue to follow price action for each candidate: no fill, near miss, touched entry, hit TP/SL, went through and returned, went through and continued, and unresolved/in-flight state.

## Implementation Phases

### Phase 1 - Future Capture Correctness

Patch the live append path so new candidates and pending intents carry enough metadata the first time:

- `src/components/forward_capture.py`
  - Preserve full decision-time `h1_setup`, `m15_confirmation`, `frameworks_evaluated`, selector metadata, trade parameters, verifier output, and external confluence source status in `strategy_follow_candidates.jsonl`.
  - Add Sierra `source_status` and `parity_status` fields.
  - Add Databento trigger-policy fields without making paid requests.
- `src/components/execution.py`
  - Make pending-limit `trade_id` globally unique or symbol-qualified.
  - Persist `candidate_id`, `decision_time_utc`, `source_file`, `source_hash`, and `source_symbol` in `PendingLimitIntent`.
  - Backward-compatible load for old pending-intent JSON.
- `src/components/orchestrator.py`
  - Pass candidate telemetry into `set_limit_intent`.
  - Pass pending-intent identity back into lifecycle checks when a limit is monitored.
- `src/components/shadow_observer.py`
  - Normalize status rows with canonical top-level counters and timestamps.
- `scripts/follow_live_candidate_paths.py`
  - Keep following every live candidate after each M15 close.
  - Run the gap-closure resolver after path follow so candidate summaries update automatically.

Validation:

- Unit tests for candidate capture fields, pending-intent serialization, lifecycle telemetry, and observer status shape.
- `scripts/verify_shadow_log_integrity.py` must validate the new schemas.
- `scripts/_live_monitor_iter.py` must include freshness checks for new closure logs.

### Phase 2 - Backfill and Resolver Rows

Add one reusable backfill/resolver module plus a script:

- `src/research_infra/live_shadow_gap_closure.py`
- `scripts/close_live_shadow_capture_gaps.py`

The script must read existing live logs and raw market data, then append recovery rows. It must not rewrite historical JSONL files.

Expected new append-only logs:

- `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl`
- `shadow_logs/live_structural_strategy_metadata.jsonl`
- `shadow_logs/v2b_forward_pair_resolutions.jsonl`
- `shadow_logs/prefill_delivery_path_resolutions.jsonl`
- `shadow_logs/fvg_ob_confluence_resolutions.jsonl`
- `shadow_logs/missed_opportunity_shadow.jsonl`
- `shadow_logs/candidate_ltf_path_order.jsonl`
- `shadow_logs/databento_live_trigger_decisions.jsonl`
- `shadow_logs/sierra_confluence_source_status.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- `shadow_logs/account_truth_reconciliation_status.jsonl`
- `shadow_logs/proxy_blocker_status.jsonl`
- `shadow_logs/ml_shadow_status.jsonl`
- `shadow_logs/external_source_blocker_status.jsonl`

Validation:

- Backfill script exits non-zero on corrupt input rows unless those rows are quarantined and documented.
- Re-running the backfill script must be idempotent by deterministic row key.
- Verifier must report zero duplicate keys in all closure logs.

## Gap Register

### Gap 1 - V2/V3 Structural and Reentry Systems Not Live-Scorable

Fix:

- Capture full selector metadata for future candidates.
- Add `live_structural_strategy_metadata.jsonl` rows for every existing candidate using available candidate, V2b, pre-fill, FVG/OB, and mechanical shadow rows.
- Modify mechanical shadow scoring to consume structural metadata when present.

Backfill:

- For values recoverable from existing rows, write `RECOVERED_EXACT`.
- For values recoverable from MT5 M1/M15 slices, write `RECOVERED_DERIVED`.
- For standalone FVG geometry, lock/reentry timestamps, or cost-aware min-R fields that were never captured, write `SOURCE_NOT_CAPTURED` instead of fabricating.

Done when:

- Each of the 8 live candidates has one structural metadata row.
- Each affected strategy has either a computed outcome row or an explicit source-captured blocker row keyed to the candidate.
- No latest row is silently `MISSING_REQUIRED_LIVE_METADATA` without a companion closure explanation.

### Gap 2 - Pending-Limit Lifecycle Rows Cannot Join Safely

Fix:

- Symbol-qualify or globally uniquify pending `trade_id`.
- Persist candidate identity in pending intents and lifecycle rows.
- Add join verifier that rejects duplicate lifecycle keys.

Backfill:

- Match old lifecycle rows to candidates by `symbol`, `source_symbol`, side, entry, stop, take-profit, and nearby decision time.
- For XAUUSD and NAS100 `lim_2026-05-04_0715`, write separate backfill rows proving the symbol/price disambiguation.

Done when:

- Existing 17 lifecycle rows have join-backfill rows where unambiguous.
- Future lifecycle rows carry non-null `candidate_id` and `decision_time_utc`.

### Gap 3 - V2b, Pre-Fill, and FVG/OB Ledgers Are Placeholders

Fix:

- Add resolver rows per candidate for `v2b`, `prefill`, and `fvg_ob`.
- Keep original decision-time rows untouched.

Backfill:

- Join `candidate_path_follow.jsonl` and `live_mechanical_strategy_shadow_outcomes.jsonl` into resolution rows.
- Include `asof_latest_candle_utc`, fill state, TP/SL touch state, path label, bars elapsed, and no-leak status.

Done when:

- All 8 existing candidates have resolver rows for all three ledgers.
- New candidates get resolver rows on each follow-up pass.

### Gap 4 - Missed-Opportunity Comparator Absent

Fix:

- Add a shadow-only comparator for:
  - limit entry outcome
  - market-at-decision-close outcome
  - proximity-entry outcome
  - no-fill but TP/SL area reached

Backfill:

- Use candidate path rows plus MT5 M1/M15 slices where available.
- Mark XAUUSD 07:15 SHORT and NAS100 07:15 LONG as limit near-miss cases if the reconstructed path confirms TP1 area reached without entry touch.

Done when:

- Every candidate has a missed-opportunity row.
- The row explicitly states whether price missed, touched, crossed and returned, crossed and continued, or remains unresolved.

### Gap 5 - Lower-Timeframe Path Ordering Missing

Fix:

- Add M1/tick path-order rows keyed by candidate.
- Include first touch times for entry, TP1, SL, midpoint/proximity, and ambiguity status.

Backfill:

- Use MT5 M1 bars for every candidate window where available.
- If M1 is unavailable, write `SOURCE_BLOCKED` with requested range and broker symbol.
- Use tick data only when local captured tick files cover the candidate window; do not infer tick order from missing tick data.

Done when:

- Every candidate has a lower-timeframe path-order row.
- Same-bar ambiguity is reduced where M1/tick data exists, and explicitly retained where it does not.

### Gap 6 - Databento Live Confluence Trigger Policy Missing

Fix:

- Add a deterministic trigger-decision log.
- Do not poll every candle.
- Do not make paid requests in this closure pass.

Backfill:

- Write trigger-decision rows for all 8 candidates:
  - `NO_TRIGGER` when the strategy/source does not require Databento.
  - `TRIGGER_ELIGIBLE_BUT_DISABLED_BY_ENV` when a candidate would qualify but live Databento is disabled.
  - `SOURCE_BLOCKED` when a source mapping is not defined.

Done when:

- `databento_live_trigger_decisions.jsonl` exists and is fresh.
- Every row states `paid_data_calls=0` and `paid_fetch_attempted=false`.

### Gap 7 - XAGUSD/SI Sierra Source-Definition Warning Missing

Fix:

- Add `source_status` and `parity_status` to future Sierra confluence fields.
- Add a companion source-status log for existing candidates.

Backfill:

- Mark XAGUSD/SI rows as captured but interpretation-blocked until SI depth parity is validated.
- Mark NAS100/NQ and other validated mappings with their correct parity state.

Done when:

- Every candidate with Sierra features has a source-status row.
- XAGUSD/SI cannot appear as validated Databento-equivalent confluence.

### Gap 8 - Shadow Observer Status Rows Weak

Fix:

- Normalize status rows with:
  - `status`
  - `latest_closed_m15_utc`
  - `rows_written`
  - `ai_calls`
  - `databento_calls`
  - `order_calls`
  - `paid_data_calls`
  - `paid_fetch_attempted`

Backfill:

- Existing observer rows are not rewritten.
- Add new normalized status rows on next observer emission.

Done when:

- Verifier accepts the normalized shape.
- Live monitor checks observer status freshness and counters.

### Gap 9 - Session Volatility and US30 Sweep Logs Missing

Fix:

- Verify the scripts' output paths and cadence.
- Create event or no-event status rows/files so missing files do not mean "unknown."

Backfill:

- Run the monitors over the available live-session window.
- If no qualifying events exist, write explicit `NO_EVENT_IN_WINDOW` rows.

Done when:

- `session_volatility_log.csv` and `sweep_divergence_log.csv` exist with current-date rows or documented no-event rows.
- Verifier differentiates "no event" from "not running."

### Gap 10 - Candidate Snapshot Rows Permanently Unresolved

Fix:

- Add `live_candidate_strategy_rollups.jsonl` as the one-row-per-candidate latest summary for monitoring.

Backfill:

- Join candidate snapshot, path follow, mechanical outcome, resolver rows, source statuses, and lifecycle joins.

Done when:

- Every candidate has a rollup row.
- The rollup names unresolved systems and why they are unresolved.

### Gap 11 - Broker Actual-R / Account Truth Not Automated Enough

Fix:

- Add an account-truth reconciliation status lane that separates:
  - `ACCOUNT_HISTORY_REALIZED`
  - `LIVE_R_ARTIFACT`
  - `RESEARCH_MEASURED`
  - `NO_OPEN_POSITION`
  - `HISTORY_NOT_AVAILABLE`

Backfill:

- Query read-only MT5 account/history if available.
- If unavailable, write explicit status rows and do not make dollar/R claims from shadow artifacts.

Done when:

- Every trade/candidate rollup can state whether actual realized account truth exists.

### Gap 12 - GBPJPY Direct Futures Proxy Missing

Fix:

- Add a proxy-blocker status row for GBPJPY until a validated 6B/6J or other proxy design exists.

Backfill:

- Write a current blocker row so GBPJPY confluence absence is intentional and visible.

Done when:

- GBPJPY rows cannot silently imply missing source equals no signal.

### Gap 13 - ML/K55 Shadow Predictions Missing

Fix:

- Add a status lane for ML/K55 shadow predictions.
- Do not activate model inference without target refresh and owner approval.

Backfill:

- Write `APPROVAL_OR_TARGET_REFRESH_BLOCKED` status rows for current candidates if the lane remains in the follow-data program.

Done when:

- The monitoring summary shows ML/K55 as blocked, not forgotten.

### Gap 14 - Broader Source/Pre-Registration Items Blocked

Scope:

- ES/MES, CL, ZN, VIX/VXM, options/gamma, older-data source items, and any other research items deferred specifically for forward/live source confirmation.

Fix:

- Add an external-source blocker status lane.
- Keep these out of live candidate decisions until source, cadence, proxy, and pre-registration rules exist.

Backfill:

- Write status rows naming each blocked source family and the missing prerequisite.

Done when:

- The live monitoring summary distinguishes active capture, no-event capture, and source/pre-registration blockers.

## Cross-Cutting Checks

### Data Preservation and Non-Overwrite

- Never rewrite original live JSONL rows during closure.
- New rows must include deterministic `row_key`.
- Verifier checks duplicate `row_key` values.
- Use atomic/locked append helpers where available.

### Staleness

- Add freshness checks for every new closure log.
- Candidate-level rollup must state `latest_follow_asof_utc`.
- A candidate is stale if a newer M15 close exists but no path/resolver/rollup row exists after it.

### Candidate Chart Monitoring

For each candidate and each strategy lane, track:

- distance to entry
- nearest approach
- first entry touch
- first TP1 touch
- first SL touch
- crossed entry and returned
- crossed entry and continued
- reached TP/SL area without entry
- unresolved/in-flight

### No Cost or Live Decision Side Effects

Closure pass must report:

- `ai_calls=0`
- `canary_calls=0`
- `order_calls=0`
- `paid_data_calls=0`
- no changes to prompt files
- no changes to production trading gates

## Completion Checklist

- [x] Future capture emits complete candidate, pending lifecycle, source-status, and observer metadata.
- [x] All 14 audit gaps have append-only closure/backfill rows or explicit blocker rows.
- [x] All current live candidates have candidate rollups.
- [x] XAUUSD 07:15 and NAS100 07:15 near-miss behavior is recorded in missed-opportunity rows.
- [x] XAGUSD/SI source-warning rows exist.
- [x] Databento trigger-decision rows exist with zero paid fetches.
- [x] Session volatility and sweep divergence status rows/files exist.
- [x] Integrity verifier covers all new logs and duplicate keys.
- [x] Live monitor checks new log freshness.
- [x] Targeted tests pass.
- [x] `.context/00_core/research_current_state.md` points to this plan and the final closure artifact.
- [x] Final closure artifact records what was fixed, what was exactly backfilled, what was derived, and what remains source-blocked.
