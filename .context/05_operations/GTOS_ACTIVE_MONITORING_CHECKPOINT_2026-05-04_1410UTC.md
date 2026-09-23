# GTOS Active Monitoring Checkpoint - 2026-05-04 14:10 UTC

Status: monitoring continues under active goal
Owner: Codex
Scope: NY shadow-capture gap repair, restart, and data-health validation

## Control Plane

- `_live_monitor_iter.py` at `14:10 UTC`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- The orchestrator fleet was restarted to load the shadow-capture fix. Direct `Start-Process` / tool-launched watchdog children did not survive this shell job context, so the existing Windows scheduled task `TradingAgentDaily` was triggered and produced durable PIDs:
  - `XAUUSD=17948`, `US30_cash=22904`, `USDJPY=22972`, `GBPJPY=22568`, `GBPUSD=20964`, `XAGUSD=22208`, `NAS100=17388`.
- `psutil.pid_exists` confirmed all 7 scheduled-task PIDs were alive after launch.
- MT5 account truth before restart: no open positions and no pending broker orders.
- The owner-approved canary-skip marker remained active; restart logs show `[canary] OWNER-APPROVED SKIP`, not a canary subprocess run.

## Gap Found

- The 13:15 and 13:30 NAS100 production trade records existed, but `strategy_follow_candidates.jsonl` initially missed both rows.
- Root cause class: the live orchestrator can save the trade record before all research-only forward-shadow rows finish. If the process is interrupted in that window, the trade record is the original decision-time source of truth but the candidate shadow row can be missing.
- The previous data-health audit did not catch this because it only treated `strategy_follow_candidates.jsonl` as source of truth.

## Fixes Implemented

- Added `src/research_infra/trade_record_candidate_backfill.py`.
  - It scans `knowledge_base/trade_records/*/*.json` for AI `CANDIDATE` records.
  - It derives candidate IDs from filenames first, so existing candidates are skipped without opening large JSON files.
  - It appends missing point-in-time candidate rows through `record_live_candidate_forward_shadow`.
  - It is duplicate-safe and declares `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.
- `scripts/follow_live_candidate_paths.py --max-hours 12` now runs trade-record reconciliation before path/mechanical/rollup work.
- `scripts/audit_live_shadow_data_health.py` now compares trade-record CANDIDATEs against latest strategy-follow candidates and reports missing or mismatched rows.
- `src/research_infra/forward_capture.py` now defaults Sierra candidate confluence to immediate source/status capture with full feature extraction deferred outside the candidate write path. This prevents a large live `.depth` file from blocking shadow candidate capture.
- Added `scripts/repair_jsonl_invalid_rows.py` to quarantine invalid JSONL fragments under lock before rewriting a clean file.
- The opportunity audit now treats `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP` primaries as intentionally suppressed, not corrupt duplicate counting.

## Backfill Applied

- `sync_trade_record_candidates(max_hours=12)` wrote:
  - `NAS100_2026-05-04T13:15:00+00:00`
  - `NAS100_2026-05-04T13:30:00+00:00`
  - `NAS100_2026-05-04T14:00:00+00:00`
- All were recovered from the original trade records; no synthetic future-derived fields were fabricated.

## Shadow Pipeline Validation

Latest post-restart/pass state:

- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=27`, `candidate_path_follow rows_written=27`, `live_mechanical_strategy_shadow_outcomes rows_written=432`, gap closure completed, all no-call flags clean.
- `summarize_live_shadow_opportunities.py`: `27` raw candidates, `8` countable primary opportunities, `18` duplicate active setup rows, `1` same-symbol overlap suppressed.
- `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=32072`.
- `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=27`, trade-record coverage `27/27`, no value mismatches.
- External confluence health: Sierra objects present for all candidates; `20` full-feature rows from earlier inline extraction, `3` deferred NAS100 rows with exact source file status/path/mtime/size, `4` no registered proxy rows. Databento remained local/cache/trigger-status only with `paid_fetch_attempted=false`, `paid_data_calls=0`.

## JSONL Repair

- The force restart left one invalid fragment in `shadow_logs/strategy_follow_evaluations.jsonl`: raw line `ull}`.
- `scripts/repair_jsonl_invalid_rows.py --apply shadow_logs/strategy_follow_evaluations.jsonl` quarantined it to `research/program_control/JSONL_INVALID_ROW_QUARANTINE_2026-05-04.jsonl` with hash `8e24ddcec789c70524c81f1b847f36cc30a73d7f3bf5c746839ba44dbb8a3ac3`, then rewrote the file with valid rows only.
- This was a malformed write fragment, not a valid decision row.

## Validation Commands

- `python -m py_compile src\research_infra\forward_capture.py src\research_infra\trade_record_candidate_backfill.py scripts\follow_live_candidate_paths.py scripts\audit_live_shadow_data_health.py scripts\repair_jsonl_invalid_rows.py`
- `python -m pytest tests\test_follow_live_candidate_paths.py tests\test_live_shadow_data_health_audit.py tests\test_repair_jsonl_invalid_rows.py -q -p no:cacheprovider --basetemp C:\tmp\gtos_pytest_shadow_health_20260504_1410` -> `16 passed`.

## Current Interpretation

- The critical capture gap is closed for the observed missed candidates.
- Future live candidate shadow writes no longer depend on full Sierra heatmap parsing completing inline.
- `SOURCE_NOT_CAPTURED` structural fields remain explicit limitations and must not be backfilled from later candles unless the exact original decision-time source row is found.
- For trade-opportunity comparisons, use only latest `opportunity_counting_status=COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`; raw candidate/mechanical rows remain evidence but include duplicates and active-overlap suppressions.

## Next

- Continue monitoring into the next 14:15 UTC M15 boundary.
- After the next candidate, verify that new live candidate rows show Sierra source/status capture immediately rather than blocking on full `.depth` feature extraction.

## 14:16 UTC Follow-Up

- `_live_monitor_iter.py` at `14:16 UTC`: latest candle `2026-05-04T14:15:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- Required writer/reader order was rerun after the 14:15 boundary:
  - `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=29`, `candidate_path_follow rows_written=28`, `live_mechanical_strategy_shadow_outcomes rows_written=448`, trade-record reconciliation `rows_written=0` because all 29 candidate trade records were already shadowed.
  - `summarize_live_shadow_opportunities.py`: `29` raw candidates, `8` countable primary opportunities, `20` duplicate active setup rows, `1` same-symbol overlap suppressed.
  - `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=32834`.
  - `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=29`, `raw_rows_inspected=9484`.
- New 14:15 raw candidates were `NAS100_2026-05-04T14:15:00+00:00` and `XAGUSD_2026-05-04T14:15:00+00:00`; both were preserved as raw evidence and classified as `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`, so they do not inflate trade/opportunity results.
- Trade levels remain preserved under each row's `trade_parameters`; they are not top-level fields in `strategy_follow_candidates.jsonl` or `candidate_path_follow.jsonl`.

## 14:46 UTC Pending-Lifecycle Scoring Repair

- A second live-shadow scoring issue was found after the 14:30 pass: `PENDING_LIMIT_LIFECYCLE` mechanical rows were using generic M15 candidate-path scoring even when the production candidate had actually created an internal live limit intent.
- Concrete example: `GBPJPY_2026-05-04T03:00:00+00:00` had `final_outcome_at_log=LIMIT_PLACED`. Generic path said entry and SL were touched, but `pending_limit_lifecycle.jsonl` showed the internal intent was cancelled wrong-side/no-fill at 04:00 UTC. Treating that as a filled -1R trade was not lifecycle truth.
- `src/research_infra/live_mechanical_shadow.py` now scores `PENDING_LIMIT_LIFECYCLE` from `pending_limit_lifecycle.jsonl` when a real limit intent existed, matching by `candidate_id` when present and otherwise by exact symbol/side/entry/SL/TP geometry. Generic candidate-path scoring remains only for hypothetical/non-placed candidates.
- Existing incorrect rows were not rewritten. The follow pass appended explicit correction rows with `correction_reason=latest_computed_shadow_outcome_changed_after_source_reconciliation`; readers use the latest `created_at_utc` row.
- `scripts/verify_shadow_log_integrity.py` now allows only those explicitly marked append-only mechanical correction rows to supersede a prior `(candidate_id, strategy_id, asof_latest_candle_utc)` key; unmarked duplicates still fail.
- `src/research_infra/live_shadow_gap_closure.py` now emits candidate/status-aware pending lifecycle join keys so old `SOURCE_NOT_CAPTURED` joins can be superseded append-only when candidate rows later make an exact match possible.
- After repair and the 14:45 candle:
  - `_live_monitor_iter.py`: latest candle `2026-05-04T14:45:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
  - `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=32`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls.
  - `summarize_live_shadow_opportunities.py`: `32` raw candidates -> `9` countable primary opportunities and `23` duplicates.
  - `PENDING_LIMIT_LIFECYCLE` corrected summary: `+0.5R`, with `3` rows sourced from internal pending lifecycle telemetry. Baseline and V2 OB-boundary proxy summaries remain `-0.5R`, so pending lifecycle truth materially differs from generic path proxy.
  - `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
  - `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=32`.
- New 14:45 raw candidate: `XAGUSD_2026-05-04T14:45:00+00:00`, `REJECTED_L2`, duplicate of active XAGUSD short opportunity, path label `continued_without_entry_touch_to_tp_area`; preserved but not counted as a new opportunity.
- Validation: `py_compile` passed for lifecycle scorer/gap closure/summary/verifier; targeted pytest passed with `26 passed`.

## 15:01 UTC Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T15:00:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=33`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls.
- `summarize_live_shadow_opportunities.py`: `33` raw candidates -> `9` countable primary opportunities and `24` duplicates.
- `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
- `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=33`.
- Corrected strategy snapshot remains stable: `PENDING_LIMIT_LIFECYCLE=+0.5R`; `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-0.5R`; `V2_STRUCT_OB_BOUNDARY=-0.5R`; `V2B_OB_BOUNDARY_PROSPECTIVE=-0.5R`.
- New 15:00 raw candidate: `XAGUSD_2026-05-04T15:00:00+00:00`, `REJECTED_L2`, duplicate of an active XAGUSD short opportunity. Latest path label is `continued_without_entry_touch_to_tp_area`, so it is preserved but not counted as a separate opportunity.

## 15:17 UTC Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T15:15:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=35`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls.
- `summarize_live_shadow_opportunities.py`: `35` raw candidates -> `9` countable primary opportunities and `26` duplicates.
- `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
- `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=35`.
- New 15:15 raw candidates: `XAGUSD_2026-05-04T15:15:00+00:00` and `NAS100_2026-05-04T15:15:00+00:00`. Both were duplicate active setup rows and both latest paths were `continued_without_entry_touch_to_tp_area`.

## 15:50 UTC LTF Terminal-Order Repair

- A third data-quality issue was found and fixed: M15 path rows labeled `entry_touched_tp_and_sl_m15_ambiguous` were not using lower-timeframe post-entry ordering before proxy-R summarization. The summary fallback could therefore count unresolved same-candle ambiguity as flat `0R`.
- `src/research_infra/live_shadow_gap_closure.py` now writes explicit LTF terminal fields on `candidate_ltf_path_order.jsonl`:
  - `terminal_outcome_status`
  - `terminal_event_utc`
  - `terminal_event_r`
  - `terminal_order_ambiguity`
- The terminal rule is strict: TP/SL touches before entry are not filled-trade terminal events. Only the first TP/SL after entry can score R. Entry and TP/SL in the same M1 bar remain ambiguous and do not contribute R without tick-order proof.
- `src/research_infra/live_opportunity_dedupe.py` now resets opportunities only from resolved post-entry LTF terminal events. Same-M1 terminal ambiguity does not reset a same-symbol active setup.
- `src/research_infra/live_mechanical_shadow.py` now:
  - reads `candidate_ltf_path_order.jsonl`,
  - resolves M15 TP/SL ambiguity from LTF terminal evidence where possible,
  - appends correction rows with explicit `strategy_proxy_r`,
  - marks unresolved same-M1 ambiguity as non-R-counted evidence.
- `scripts\summarize_live_shadow_opportunities.py` now counts `COMPUTED_FROM_LTF_PATH_ORDER` rows and leaves unresolved ambiguity out of R.
- `scripts\audit_live_shadow_data_health.py` now treats blocked same-symbol-overlap primaries plus their duplicates as intentionally suppressed rather than corrupt primary counts.
- Validation: targeted escalated pytest passed with `41 passed`.
- Backfill applied via `follow_live_candidate_paths.py --max-hours 12`:
  - First pass saw `38` candidates, wrote `35` new path rows, `35` LTF rows, and `8928` append-only mechanical correction rows because prior rows needed explicit LTF/proxy-R corrections.
  - Second pass wrote only `50` additional mechanical correction rows to relabel older ambiguity rows that had an old LTF row without terminal fields.
- Final sequential health state after repair:
  - `_live_monitor_iter.py`: latest candle `2026-05-04T15:45:00+00:00`, `crit=0`, `anom=0`, `pids=4`, `open_pos=0`. `pids=4` is expected because USDJPY, GBPJPY, and GBPUSD were outside their KZs.
  - `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=38`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls.
  - `summarize_live_shadow_opportunities.py`: `38` raw candidates -> `8` countable primary opportunities, `29` duplicate active setup rows, and `1` blocked active same-symbol overlap.
  - `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=46795`.
  - `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=38`, `raw_rows_inspected=23021`.
- Corrected countable proxy-R snapshot:
  - `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-1.5R` over `7` R-counted rows, with `1` same-M1 ambiguous row preserved but not R-counted.
  - `PENDING_LIMIT_LIFECYCLE=+0.5R` over `7` R-counted rows, with `3` rows sourced from internal pending lifecycle telemetry and `1` same-M1 ambiguous row preserved but not R-counted.
  - `V2_STRUCT_OB_BOUNDARY=-1.5R` and `V2B_OB_BOUNDARY_PROSPECTIVE=-1.5R` over `7` R-counted rows each.
  - V2/V3 structural-lock and FVG variants remain `NOT_SCORED` because their decision-time metadata is still `SOURCE_NOT_CAPTURED`; do not fabricate those fields from later candles.
- New 15:45 raw candidates: `XAGUSD_2026-05-04T15:45:00+00:00` and `NAS100_2026-05-04T15:45:00+00:00`; both were preserved as duplicate active setup evidence and not counted as separate opportunities.
- No restart is required for this repair. The affected scripts are monitoring/backfill/reporting helpers run manually by the active monitoring goal; live orchestrator trading logic was not changed.

## 16:02 UTC Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T16:00:00+00:00`, `crit=0`, `anom=0`, `pids=3`, `open_pos=0`. `pids=3` is expected after US30 NY KZ ended at 16:00 UTC; active KZ symbols remain XAUUSD, XAGUSD, and NAS100.
- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=40`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls. The writer appended `37` path rows, `37` LTF rows, and `592` mechanical rows for the 16:00 as-of.
- `summarize_live_shadow_opportunities.py`: `40` raw candidates -> `8` countable primary opportunities, `31` duplicate active setup rows, and `1` blocked active same-symbol overlap.
- `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=47749`.
- `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=40`, `raw_rows_inspected=23927`.
- New 16:00 raw candidates:
  - `XAGUSD_2026-05-04T16:00:00+00:00`: `REJECTED_L2`, SHORT `ob_retest`, entry `75.471`, SL `75.968`, TP1 `74.726`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
  - `NAS100_2026-05-04T16:00:00+00:00`: `REJECTED_GATE1_SAFETY`, LONG `ob_retest`, entry `27446.2`, SL `27387.9`, TP1 `27533.6`; duplicate active setup under an active same-symbol overlap; path `continued_without_entry_touch_to_tp_area`.
- Corrected countable proxy-R snapshot remained stable after the 16:00 pass: `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-1.5R`, `PENDING_LIMIT_LIFECYCLE=+0.5R`, `V2_STRUCT_OB_BOUNDARY=-1.5R`, `V2B_OB_BOUNDARY_PROSPECTIVE=-1.5R`. Same-M1 ambiguity remains excluded from R.

## 16:16 UTC Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T16:15:00+00:00`, `crit=0`, `anom=0`, `pids=3`, `open_pos=0`.
- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=42`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls. The writer appended `39` path rows, `39` LTF rows, and `624` mechanical rows for the 16:15 as-of.
- `summarize_live_shadow_opportunities.py`: `42` raw candidates -> `8` countable primary opportunities, `33` duplicate active setup rows, and `1` blocked active same-symbol overlap.
- `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=48740`.
- `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=42`, `raw_rows_inspected=24881`.
- New 16:15 raw candidates:
  - `XAGUSD_2026-05-04T16:15:00+00:00`: `REJECTED_L2`, SHORT `ob_retest`, entry `75.471`, SL `75.977`, TP1 `74.712`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
  - `NAS100_2026-05-04T16:15:00+00:00`: `REJECTED_GATE1_SAFETY`, LONG `ob_retest`, entry `27446.2`, SL `27385.6`, TP1 `27537.1`; duplicate active setup under an active same-symbol overlap; path `continued_without_entry_touch_to_tp_area`.
- Countable proxy-R snapshot remained stable: `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-1.5R`, `PENDING_LIMIT_LIFECYCLE=+0.5R`, `V2_STRUCT_OB_BOUNDARY=-1.5R`, `V2B_OB_BOUNDARY_PROSPECTIVE=-1.5R`.

## 16:32 UTC Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T16:30:00+00:00`, `crit=0`, `anom=0`, `pids=3`, `open_pos=0`.
- First reader pass after 16:30 intentionally failed strict semantic health because two candidate rows were written after the follow writer snapshot:
  - `XAGUSD_2026-05-04T16:30:00+00:00` was created at `2026-05-04T16:30:23.741290+00:00`.
  - `NAS100_2026-05-04T16:30:00+00:00` was created at `2026-05-04T16:30:26.970798+00:00`.
- This was a read-after-new-candidate race, not a persistent capture gap. Rerunning `follow_live_candidate_paths.py --max-hours 12` immediately closed it: `candidates_seen=44`; the writer appended `2` path rows, `2` LTF rows, `32` mechanical rows, and the dependent source/rollup/opportunity rows; trade-record reconciliation wrote `0`.
- Clean post-rerun readers:
  - `summarize_live_shadow_opportunities.py`: `44` raw candidates -> `8` countable primary opportunities, `35` duplicate active setup rows, and `1` blocked active same-symbol overlap.
  - `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=49781`.
  - `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=44`, `raw_rows_inspected=25883`.
- New 16:30 raw candidates:
  - `XAGUSD_2026-05-04T16:30:00+00:00`: `REJECTED_L2`, SHORT `ob_retest`, entry `75.471`, SL `75.98`, TP1 `74.707`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`. Sierra source `SIM26-COMEX.2026-05-04.depth` captured with mtime `2026-05-04T16:30:19.591561+00:00`; Databento source blocked for SI with `paid_fetch_attempted=false`, `paid_data_calls=0`.
  - `NAS100_2026-05-04T16:30:00+00:00`: `REJECTED_GATE1_SAFETY`, LONG `ob_retest`, entry `27446.2`, SL `27385.6`, TP1 `27537.1`; duplicate active setup under an active same-symbol overlap; path `continued_without_entry_touch_to_tp_area`. Sierra source `NQM26-CME.2026-05-04.depth` captured with mtime `2026-05-04T16:30:24.593763+00:00`; Databento NQ trigger was eligible but disabled by env with `paid_fetch_attempted=false`, `paid_data_calls=0`.
- Countable proxy-R snapshot remained stable: `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-1.5R`, `PENDING_LIMIT_LIFECYCLE=+0.5R`, `V2_STRUCT_OB_BOUNDARY=-1.5R`, `V2B_OB_BOUNDARY_PROSPECTIVE=-1.5R`. Same-M1 ambiguity remains preserved but excluded from R.

## 17:28 UTC Sierra Feature-Lane Repair And Monitoring Pass

- `_live_monitor_iter.py`: latest candle `2026-05-04T17:15:00+00:00`, `crit=0`, `anom=0`, `pids=0`, `open_pos=0`. This is expected because all monitored kill zones had ended by 17:00 UTC.
- `follow_live_candidate_paths.py --max-hours 12`: `candidates_seen=48`; trade-record reconciliation `rows_written=0`; no AI/canary/execution/paid data calls. The writer refreshed candidate path, LTF order, mechanical outcome, resolution, blocker, rollup, and opportunity rows for the 17:15 as-of.
- New raw candidates since the 16:30 checkpoint:
  - `XAGUSD_2026-05-04T16:45:00+00:00`: `REJECTED_L2`, SHORT `ob_retest`, entry `75.471`, SL `75.98`, TP1 `74.707`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
  - `NAS100_2026-05-04T16:45:00+00:00`: `REJECTED_GATE1_SAFETY`, LONG `ob_retest`, entry `27446.2`, SL `27385.6`, TP1 `27537.1`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
  - `XAGUSD_2026-05-04T17:00:00+00:00`: `REJECTED_L2`, SHORT `ob_retest`, entry `75.471`, SL `75.967`, TP1 `74.727`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
  - `NAS100_2026-05-04T17:00:00+00:00`: `REJECTED_GATE1_SAFETY`, LONG `ob_retest`, entry `27446.2`, SL `27387.1`, TP1 `27534.8`; duplicate active setup; path `continued_without_entry_touch_to_tp_area`.
- Sierra candidate enrichment is now split into a dedicated append-only feature lane:
  - Candidate rows continue to capture exact Sierra source/status/path/mtime/size immediately.
  - `scripts\enrich_sierra_live_candidate_depth_features.py --max-hours 24 --pending-status-only` gives every candidate an explicit feature-lane state without running heavy `.depth` scans in the monitoring foreground.
  - Current coverage: `21` `FEATURES_EXTRACTED`, `24` `FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN`/deferred heavy scan rows, and `3` `NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL` rows for GBPJPY.
  - A repeat status-only enrichment wrote `0` rows (`already_extracted=21`, `duplicate_file_state=27`), so the row-keying is stable and not churning duplicate status rows.
- `scripts\extract_sierra_depth_features.py` now replays depth from the last `CLEAR_BOOK` before the pre-decision window instead of midnight, which keeps full feature backfills no-leak while reducing unnecessary scan volume. Full NQ/SI extraction remains heavy backfill work and must not block candidate capture.
- `scripts\audit_live_shadow_data_health.py` and `scripts\verify_shadow_log_integrity.py` now know `sierra_depth_feature_snapshots.jsonl`. The health audit requires candidate coverage and treats `depth_path`, `sierra_futures_symbol`, and `sierra_source_symbol` nulls as documented only when `feature_status=NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL`.
- Final sequential readers after the Sierra audit fix:
  - `summarize_live_shadow_opportunities.py`: `48` raw candidates -> `8` countable primary opportunities, `39` duplicate active setup rows, and `1` blocked active same-symbol overlap.
  - `verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=53261`.
  - `audit_live_shadow_data_health.py`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=48`, `raw_rows_inspected=29257`, `unexpected_null_counts={}`, `critical_null_counts={}`.
- Countable proxy-R snapshot remains: `LIVE_AI_J46_J49_BASELINE_COMPARATOR=-1.5R`, `PENDING_LIMIT_LIFECYCLE=+0.5R`, `V2_STRUCT_OB_BOUNDARY=-1.5R`, `V2B_OB_BOUNDARY_PROSPECTIVE=-1.5R`. Same-M1 ambiguity remains preserved but excluded from R.
- Databento remained trigger-status/local-cache only in this monitoring lane: `paid_fetch_attempted=false`, `paid_data_calls=0`. No restart is required for the Sierra feature-lane repair because the affected pieces are monitoring/backfill/reporting scripts, not live trading decision code.
