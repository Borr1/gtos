# Live Monitoring Ledger - 2026-05-04

Status: active
Goal source: `.context/05_operations/GTOS_FULL_DAY_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-04.md`
Posture: observational monitoring only; no trading decisions; no canary or AI/API spend unless owner explicitly approves.

## 2026-05-04 06:21 UTC / 14:21 MYT

- Goal state: active.
- Scope confirmed additive: MT5, Sierra, orchestrators, tick capture, watchdog, notification queue, storage, shadow/follow-data rows, candidate path follow, pending-limit lifecycle, source blockers, stale-data checks, non-duplicate/append-only preservation.
- Baseline health:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
  - `scripts/watchdog_e2e_verify.py --verbose`: PASS earlier in resumed session; latest `logs/watchdog.log` shows 17 healthy, 0 restarted at 06:16 UTC.
  - Seven orchestrator lock PIDs found alive.
  - Seven tick-capture lock PIDs found alive.
  - Notification queue worker PID found alive; queue length 0.
  - Sierra `SierraChart_64` process found responding.
  - Core Sierra forward files `NQM26`, `MNQM26`, `ESM26`, `MESM26` `.depth` and NQ/MNQ `.scid` files observed writing at 06:19 UTC.
  - Shadow observer PID 1460 found alive and cycling every ~20s; no rows emitted yet because current observer lanes were outside active windows.
  - Candidate path follow ran with `candidates_seen=0`, `rows_written=0`; source candidate file not present yet because no live CANDIDATE rows have appeared since hooks loaded.
- Watch items checked:
  - Tick `.state.json` ages for USDJPY/XAGUSD exceeded a short 90s sample threshold, but logs showed fresh tick flushes with growing totals and watchdog showed tick-capture PIDs healthy. Current classification: false-positive / low-cadence flush signal; continue watching during active KZ.
  - An initial Sierra freshness list looked stale, but direct target-file checks showed current writes at 06:19 UTC. Current classification: false-positive.
  - UK100 MT5 tick was stale outside UK100 active window during earlier probe. Current classification: watchlist only; re-check near UK100 London window before calling it degraded.
- Pending-limit lifecycle:
  - GBPJPY Tokyo limit `lim_2026-05-04_0300` was followed through outside-KZ checks and cancelled wrong-side at 04:00 UTC after price moved beyond stop side without fill. Evidence remains in `shadow_logs/pending_limit_lifecycle.jsonl`.

Next cadence:
- Continue between-KZ checks until 07:00 UTC London start.
- At active KZ, switch to 5-minute cadence for live monitor, heartbeats, stale data, shadow/follow rows, candidate path follow, and issue escalation.

## 2026-05-04 06:36 UTC / 14:36 MYT

- Pre-London between-KZ pass:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`, candle `2026-05-04T06:30:00+00:00`.
  - Seven heartbeat files were fresh at ~8s age.
  - Tick-capture `.state.json` files were moving; oldest observed age was within low-cadence range and not corroborated by process/log failure.
  - Sierra core forward files `NQM26`, `MNQM26`, `ESM26`, `MESM26` `.depth` plus NQ/MNQ `.scid` were actively writing at ~3s age.
  - Shadow observer continued cycling every ~20s; no rows emitted yet.
  - `scripts/follow_live_candidate_paths.py`: `candidates_seen=0`, `rows_written=0`.
- Classification: no urgent or serious findings.

## 2026-05-04 06:51 UTC / 14:51 MYT

- Final pre-London pass:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`, candle `2026-05-04T06:45:00+00:00`.
  - Seven heartbeat files were fresh at ~12s age.
  - Tick-capture `.state.json` files were moving; USDJPY/XAGUSD were oldest on this sample but still corroborated by alive PIDs and recent flush logs.
  - Sierra core forward files were actively writing at ~4s age.
  - MT5 read-only probe: initialized, connected, terminal/account trade allowed, balance/equity `101223.36`, positions `0`, orders `0`.
  - MT5 core tick stream was current by broker/server clock. Raw tick epoch appears broker-time shifted ahead of UTC for active symbols, so raw negative UTC age is not used as a stale signal.
  - UK100 tick remained stale from `2026-05-01`; still outside UK100 shadow window, so watchlist only.
  - Shadow observer still outside active windows; no strategy follow rows yet.
  - `scripts/follow_live_candidate_paths.py`: `candidates_seen=0`, `rows_written=0`.
- Classification: no urgent or serious findings. UK100 remains a timed re-check item near 08:00 UTC.

## 2026-05-04 07:03-07:08 UTC / 15:03-15:08 MYT

- First active London pass:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`, candle `2026-05-04T07:00:00+00:00`.
  - Seven heartbeat files were fresh; tick-capture `.state.json` files were moving within normal cadence.
  - Shadow observer emitted first live no-AI/no-execution strategy row:
    - File: `shadow_logs/strategy_follow_evaluations.jsonl`
    - Row count: `1`
    - Row: `EURUSD`, decision candle `2026-05-04T07:00:00+00:00`, source `shadow_observer_mso_no_ai`, `source_run_id=shadow_observer_1460_20260504T060418Z`, `dedupe_key=eurusd_6e_mso_shadow_v1|2026-05-04T07:00:00+00:00|SHADOW_OBSERVER_MSO_NO_AI`
  - `scripts/follow_live_candidate_paths.py`: `candidates_seen=0`, `rows_written=0`.
- Findings:
  - `MODERATE`: EURUSD shadow observer logs `tick_features: no parquet data for EURUSD`. The strategy row is still emitted and no-AI/no-execution, but microstructure enrichment is missing because no EURUSD tick-capture daemon exists. Keep watching; do not start new collectors inside active KZ without a separate scoped decision.
  - `SERIOUS monitoring false-positive fixed`: `scripts/no_data_alert_monitor.py` was alerting from stale legacy per-symbol log mtimes even though per-symbol heartbeats and tick captures were fresh. Patched monitor to prefer fresh `pipeline_state/heartbeat_{SYMBOL}.json` and fall back to legacy logs.
- Validation:
  - `python -m py_compile scripts\no_data_alert_monitor.py`: passed.
  - `python -m pytest tests\test_no_data_alert_monitor.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_no_data_monitor_hb_escalated`: `59 passed`.
  - Live behavior check showed XAUUSD/USDJPY/GBPJPY/GBPUSD resolve `ok` via fresh heartbeat and clear prior alert state.
  - Ran `python scripts\no_data_alert_monitor.py`: cleared false alert state for XAUUSD, USDJPY, GBPJPY, GBPUSD; resulting `knowledge_base/meta/no_data_alert_state.json` is `{}`.
- Classification after fix: no urgent findings; no-data monitor false positive resolved.

## 2026-05-04 07:15-07:20 UTC / 15:15-15:20 MYT

- 07:15 M15 close:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`, candle `2026-05-04T07:15:00+00:00`.
  - Watchdog 15:16 MYT pass: 17 healthy, 0 restarted, `NO_DATA OK`.
  - Sierra NQ/MNQ/ES/MES `.depth` and NQ/MNQ `.scid` were writing at ~1s age.
  - `strategy_follow_evaluations.jsonl`: 11 rows.
  - `strategy_follow_candidates.jsonl`: 3 rows for the 07:15 decision candle.
  - `candidate_path_follow.jsonl`: path rows written for all 3 candidates after rerun.
- Candidates:
  - `XAGUSD_2026-05-04T07:15:00+00:00`: SHORT `ob_retest`, final outcome `REJECTED_L2`, blocked by `m15_choch_exists`. Sierra SI depth features extracted. Path label `entry_touched_unresolved`; hypothetical entry `75.471` touched, TP1/SL not hit yet.
  - `XAUUSD_2026-05-04T07:15:00+00:00`: SHORT `ob_retest`, final outcome `LIMIT_PLACED`, internal trade id `lim_2026-05-04_0715`, entry `4668.45`, SL `4680.26`, TP1 `4650.73`. Sierra GC depth features extracted. Path label `continued_without_entry_touch_to_tp_area`; entry not touched, TP1 area hit/continued through with last close `4607.95`.
  - `NAS100_2026-05-04T07:15:00+00:00`: LONG `ob_retest`, final outcome `LIMIT_PLACED`, internal trade id `lim_2026-05-04_0715`, entry `27736.8`, SL `27673.5`, TP1 `27831.7`. Sierra NQ depth features extracted; Databento requests remain declared/not fetched. Path label `no_touch_stayed_above_entry`; entry not touched, TP1 not hit by recorded high `27831.46` vs TP1 `27831.7`.
- Broker/account:
  - Read-only MT5 check after candidate rows: broker positions `0`, broker orders `0`.
  - `LIMIT_PLACED` is confirmed as an internal pending limit intent, not a broker pending order at that moment.
  - Active internal pending intent files:
    - `knowledge_base/meta/pending_intent_XAUUSD.pkl`
    - `knowledge_base/meta/pending_intent_NAS100.pkl`
- Classification:
  - No urgent system health issue.
  - Active monitoring item: continue following XAUUSD and NAS100 internal pending intents for entry touch, fill attempt, cancellation, wrong-side movement, or continued miss.

## 2026-05-04 07:25-07:30 UTC / 15:25-15:30 MYT

- Owner requested explicit mechanical-strategy candidate monitoring in addition to live AI candidate path follow.
- Current 07:15 candidate rows attach the full `strategy_snapshots` registry to each candidate: live/J46 baseline comparator, J46-J49 portfolio policy, S79 risk context, V2 structural selector variants, V2b OB-boundary prospective, V3 risk-bank variants, FVG/OB confluence, pre-fill delivery path, pending-limit lifecycle, and NAS100/NQ depth diagnostic.
- Verified limitation:
  - The current `strategy_snapshots` entries are registry/coverage rows with `outcome_status=UNRESOLVED_REQUIRES_FORWARD_JOIN`.
  - They prove the candidates are being tracked for those strategy families, but they do not yet compute independent per-strategy alternate entries/fills/outcomes such as "V2 would enter here" or "V3 would enter there".
  - Current live path evidence is therefore shared candidate-path evidence, not independent V2/V3 realized performance.
- Current shared path state:
  - XAGUSD SHORT: `REJECTED_L2` by `m15_choch_exists`; hypothetical entry touched, TP1/SL unresolved.
  - XAUUSD SHORT: internal pending intent at `4668.45`; entry not touched; price continued through TP1 area, so same-entry mechanical baseline is missed/no-fill so far.
  - NAS100 LONG: internal pending intent at `27736.8`; entry not touched; price stayed above entry and came within `0.24` of TP1 by recorded high.
- Monitoring stance:
  - Keep following shared candidate paths and internal pending intents during active KZ.
  - Treat independent per-strategy mechanical alternate-entry/outcome scoring as a live-shadow coverage gap to close correctly outside urgent KZ recovery work, unless another artifact is found that already produces those rows.

## 2026-05-04 07:30-07:40 UTC / 15:30-15:40 MYT

- Existing verifiers:
  - `verify_forward_capture_readiness.py`: `OK=12`, `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE_OR_NOT_YET_WIRED=1` (`databento_live_confluence`, explicit trigger/live data not enabled).
  - `audit_live_shadow_followup_coverage.py`: `ROWS_PRESENT=16`; expected blocked/waiting lanes remain documented for Databento explicit trigger, exit-trigger logs, ML/K55 approval, Component 3B/API approval, source blockers, and O1/O8/account-history verifiers.
- Added and ran reusable integrity verifier:
  - Script: `scripts/verify_shadow_log_integrity.py`.
  - Output: `research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md` / `.json`.
  - Scope: 33 JSONL files, 22,093 JSONL rows, 4 CSV shadow files, known forward-capture schemas, required fields, duplicate keys, timestamps/freshness, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, and shadow-observer safety flags.
- Result:
  - Active forward-capture logs are structurally OK: `strategy_follow_evaluations`, `strategy_follow_candidates`, `candidate_path_follow`, `v2b_forward_pairs`, `prefill_delivery_path`, `fvg_ob_confluence`, `context_control_ledger`, `pending_limit_lifecycle`, `shadow_observer_status`.
  - Candidate/path/lifecycle values passed current checks; no duplicate candidate/as-of path rows, no trade-geometry contradictions, no no-leak failures, no broker position/order mismatch.
  - Remaining integrity issue: `shadow_logs/d1_bias_lag.jsonl` has 3 malformed historical fragments at lines 153, 230, and 241 from Apr 29/30-era rows (`20}`, `": 3}`, `16}`). Latest valid D1-bias-lag row is current (`2026-05-04T07:30:05.031217+00:00`), so this is not an active trade-decision issue, but it is a real shadow-log parseability anomaly for downstream research.
- Mitigation shipped in working tree:
  - Patched `src/components/d1_bias_lag_logger.py` to serialize future appends through a lightweight sidecar file lock and fsync row writes.
  - Added targeted test coverage in `tests/test_d1_bias_lag_logger.py`.
  - Validation: `python -m py_compile scripts\verify_shadow_log_integrity.py src\components\d1_bias_lag_logger.py` passed; targeted pytest suite passed outside sandbox with temp-dir access: `39 passed`.
- Restart/load note:
  - Running orchestrators will not load the D1 lock patch until a targeted restart. Because this is a shadow-only logger issue and active KZ monitoring is healthy, do not restart solely for this during active KZ unless the owner wants the patch loaded immediately.
- 07:30 candidate/path update:
  - New `XAGUSD_2026-05-04T07:30:00+00:00` SHORT `ob_retest` candidate row logged and rejected L2 by `m15_choch_exists`; Sierra features extracted; Databento not fetched.
  - Existing XAGUSD 07:15 remains `entry_touched_unresolved`.
  - Existing XAUUSD 07:15 remains no-entry-touch and through TP1 area.
  - Existing NAS100 07:15 updated from near-TP/no-fill to through TP1 area without entry touch (`max_high=27832.71` vs TP1 `27831.7`, entry `27736.8` untouched).

## 2026-05-04 07:45-07:50 UTC / 15:45-15:50 MYT

- Active London pass:
  - `scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`, candle `2026-05-04T07:45:00+00:00`.
  - MT5 read-only check: broker positions `0`, broker orders `0`; active ticks present for XAGUSD, XAUUSD, NDX100, USDJPY, GBPJPY, GBPUSD.
  - `scripts/follow_live_candidate_paths.py`: `candidates_seen=5`, `rows_written=5`, `skipped={}`.
  - Shadow integrity verifier rerun: known forward/shadow schemas still OK; remaining issue remains the same 3 historical malformed D1-bias-lag JSONL fragments.
- Pending limits:
  - XAUUSD internal pending intent still exists: `lim_2026-05-04_0715`, SHORT entry `4668.45`, TP1 `4650.73`, SL `4680.26`, `candles_elapsed=2`.
  - NAS100 internal pending intent still exists: `lim_2026-05-04_0715`, LONG entry `27736.8`, TP1 `27831.7`, SL `27673.5`, `candles_elapsed=2`.
  - `pending_limit_lifecycle.jsonl` has inside-KZ rows at `07:45`; both remain `no_fill_still_pending`.
- Candidate path update:
  - XAGUSD 07:15: `entry_touched_unresolved`; as of `07:45`, entry touched, TP1/SL not hit, last close `75.346`.
  - XAGUSD 07:30: `entry_touched_unresolved`; as of `07:45`, entry touched, TP1/SL not hit, last close `75.346`.
  - XAGUSD 07:45: new SHORT `ob_retest` rejected L2 by `m15_choch_exists`; path row already shows entry touched, TP1/SL not hit, last close `75.346`.
  - XAUUSD 07:15: `continued_without_entry_touch_to_tp_area`; as of `07:45`, entry still not touched, TP1 area remains passed through, last close `4605.89`.
  - NAS100 07:15: `continued_without_entry_touch_to_tp_area`; as of `07:45`, entry still not touched, TP1 area passed through earlier, last close `27817.56`.
- Mechanical/follow-data interpretation:
  - Same-entry mechanical outcome for XAUUSD and NAS100 remains no-fill/missed so far despite TP-area path.
  - Independent V2/V3 alternate-entry outcomes remain registry/unresolved rows, not independently scored live outcomes.
