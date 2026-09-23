# GTOS Full-Day Active Monitoring Final Report - 2026-05-04

**Schema:** `gtos_full_day_active_monitoring_final_report_v1`  
**Generated:** `2026-05-04T19:07:08+00:00`  
**Goal source:** `.context/05_operations/GTOS_FULL_DAY_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-04.md`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Completion verdict:** `ACHIEVED_WITH_DOCUMENTED_LIMITATIONS`

## Objective Restatement

Monitor the GTOS live system through the full 2026-05-04 Tokyo, London, NY, and active shadow-observer session cycle without making trading decisions. Verify MT5, orchestrators, tick capture, Sierra Chart forward capture, Databento/cache status, watchdog, notifications, storage, shadow/follow-data logs, stale-data checks, candidate path outcomes, and append-only data health. Fix verified monitoring/data-capture issues when they are safe to fix, preserve evidence, backfill only from original decision-time sources, and produce an end-of-day report.

## Final Status

- Overall: `READY_WITH_DOCUMENTED_LIMITATIONS`.
- Final live pulse: `scripts/_live_monitor_iter.py` iteration `536`, latest candle `2026-05-04T19:00:00+00:00`, `crit=0`, `anom=0`, `pids=0`, `open_pos=0`.
- `pids=0` is expected: core production KZs closed by `17:00 UTC`, the tier-2 GER40 no-execution shadow observer closed at `19:00 UTC`, and watchdog dead-zone cleanup stops trading/tick/notification processes until the next active trading window.
- MT5 read-only probe: initialized, connected, account `0`, `trade_allowed=true`, broker orders `0`, broker positions `0`.
- Storage: `C:\` free space `61.04 GB`.
- Sierra Chart process: `SierraChart_64` PID `5056`, responding.
- Notification queue: `pipeline_state/notification_queue.jsonl` is empty. Worker restarts attempted during dead-zone were correctly killed by watchdog at `01:46` and `02:01` Malaysia time; this is expected cleanup, not an unexplained crash.
- No manual restart is needed now. Watchdog should restart required production processes when trading hours resume.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Regenerate and read `LIVE_STATE.md` | `.context/LIVE_STATE.md` regenerated at `2026-05-04T19:04:43Z`; HEAD `0e8a88cb` before final EOD patch | DONE |
| Read latest handoff and quick reference | Latest handoff `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`; `.context/00_core/quick_reference_card.md` read | DONE |
| Monitor full live stack all day | `.context/05_operations/LIVE_MONITORING_LEDGER_2026-05-04.md` plus active checkpoints and final live pulse | DONE |
| Core production closeout | Final core production KZ ended by `17:00 UTC`; final monitor `crit=0`, `anom=0`, `open_pos=0` | DONE |
| Tier-2 GER40 observer closeout | `pipeline_state/shadow_observer_state.json` records `ger40_tier2_mso_shadow_v1.last_candle_close_utc=2026-05-04T19:00:00+00:00`; outside-KZ status at `19:00:19` | DONE |
| Shadow/follow writer before readers | Final sequence ran follow writer, Sierra enrichment, summary, integrity, data-health, readiness, coverage, inventory, watchdog | DONE |
| Sierra feature/status lane | `shadow_logs/sierra_depth_feature_snapshots.jsonl`; health audit coverage `48/48`; statuses `21` extracted, `24` deferred heavy scan, `3` no proxy | DONE |
| Databento policy | `databento_live_trigger_decisions.jsonl` covers `48/48`; `databento_live_confluence.jsonl` remains waiting; `paid_fetch_attempted=false`, `paid_data_calls=0` | DONE |
| Opportunity duplicate protection | `shadow_logs/live_candidate_opportunity_clusters.jsonl`; summary counts only `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY` | DONE |
| Candidate path follow and mechanical shadows | `candidate_path_follow.jsonl`, `candidate_ltf_path_order.jsonl`, `live_mechanical_strategy_shadow_outcomes.jsonl`, and `live_candidate_strategy_rollups.jsonl` verified | DONE |
| Pending-limit lifecycle truth | `pending_limit_lifecycle.jsonl` plus mechanical corrections use internal lifecycle telemetry for real `LIMIT_PLACED` candidates | DONE |
| Trade-record candidate backfill | Health audit trade-record coverage: `48/48`, missing `[]`, value mismatches `[]` | DONE |
| Integrity verifier | `research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}` | DONE |
| Semantic data-health verifier | `research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md`: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}` | DONE |
| Forward readiness | `research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`: `OK=12`, waiting Databento live confluence `1` | DONE |
| Follow-up coverage audit | `research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`: final rows include `48` candidates, `925` path rows, `301` strategy evaluations | DONE |
| Sierra forward inventory | `research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md`: `15` ready SCID+depth symbols, `3` SCID-only cautions | DONE |
| Watchdog E2E | `scripts/watchdog_e2e_verify.py --verbose`: `WARN` only, no `FAIL`; canary cache stale is covered by active owner-approved no-canary marker | DONE |
| Notification path | Queue file is empty; worker stopped by expected watchdog dead-zone cleanup | DONE |
| Storage check | `[System.IO.DriveInfo]` showed `61.04 GB` free on `C:\` | DONE |
| No AI/canary/order/paid-data calls from monitoring | Final outputs report `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`; canary was not run | DONE |
| End-of-day output | This report | DONE |

## Final Shadow Results

- Raw candidates with latest opportunity rows: `48`.
- Countable primary opportunities: `7`.
- Not-counted evidence rows: `39` duplicate active setups and `2` blocked active same-symbol overlaps.
- Latest raw candidate outcomes: `29` `REJECTED_L2`, `16` `REJECTED_GATE1_SAFETY`, `3` `LIMIT_PLACED`.
- Latest path labels across raw candidates: `38` continued to TP area without entry touch, `5` entry touched then TP1, `3` entry touched then SL, `2` M15 TP/SL ambiguous.
- Latest path labels across countable opportunities: `3` continued to TP area without entry touch, `1` entry touched then TP1, `1` entry touched then SL, `2` M15 TP/SL ambiguous.

Countable proxy-R snapshot:

| Strategy | Proxy R | R-counted rows | Notes |
|---|---:|---:|---|
| `LIVE_AI_J46_J49_BASELINE_COMPARATOR` | `-0.5R` | `6` | Same-M1 ambiguity excluded from R |
| `PENDING_LIMIT_LIFECYCLE` | `+0.5R` | `6` | Uses internal lifecycle truth for real limit intents |
| `V2_STRUCT_OB_BOUNDARY` | `-0.5R` | `6` | Same-entry OB-boundary proxy only |
| `V2B_OB_BOUNDARY_PROSPECTIVE` | `-0.5R` | `6` | Same-entry OB-boundary proxy only |

Rows retained but not R-scored: portfolio/risk-context rows, NAS100 depth diagnostic rows, prefill/FVG/structural variants without required decision-time metadata, and same-M1 ambiguous rows without tick-order proof.

## Incidents And Actions

| Severity | Issue | Evidence | Action | Status |
|---|---|---|---|---|
| SERIOUS | No-data monitor stale-log false positive | London ledger `07:03-07:08 UTC` | Patched monitor to prefer fresh per-symbol heartbeats; tests passed | CLOSED |
| SERIOUS | D1-bias JSONL historical corrupt fragments | Integrity verifier during London | Quarantined corrupt fragments and locked future appends | CLOSED |
| SERIOUS | NAS100 heartbeat stall | `10:41 UTC` context addendum | Restarted NAS100 only; recovered `crit=0`, `anom=0` | CLOSED |
| CRITICAL DATA | Trade-record-to-shadow capture gap | NAS100 `13:15`, `13:30`, `14:00` trade records missing candidate rows | Added trade-record candidate reconciliation and backfilled from original records | CLOSED |
| SERIOUS DATA | Pending-limit lifecycle scored from generic path | GBPJPY `03:00` pending-limit example | Mechanical scorer now uses `pending_limit_lifecycle.jsonl` for real limit intents | CLOSED |
| SERIOUS DATA | M15 TP/SL ambiguity counted without LTF order | LTF repair checkpoint `15:50 UTC` | Added terminal LTF fields and excluded same-M1 ambiguity from R | CLOSED |
| SERIOUS DATA | Sierra heavy `.depth` parsing could block candidate capture | Sierra feature-lane repair `17:28 UTC` | Split immediate source capture from out-of-band feature lane | CLOSED |
| LOW/VERIFIER | Watchdog canary cache stale while canary is owner-skipped | `watchdog_e2e_verify.py --verbose` first failed canary freshness | Verifier now downgrades stale cache to WARN only while owner-approved skip is active and unexpired | CLOSED |
| LOW/REPORTING | Provisional final report treated `17:00 UTC` as all-session close | GER40 observer config shows NY `14:00-19:00 UTC` | Monitored GER40 to `19:00 UTC` and corrected this final report/context | CLOSED |
| EXPECTED | Notification queue worker stopped after session | Watchdog log shows dead-zone cleanup killed PIDs `13728`, `3908`, and `8892`; queue empty | Reclassified as expected dead-zone cleanup; no manual restart now | CLOSED |
| MODERATE/VERIFIER | Pending-limit join backfill showed false wall-clock staleness | Integrity report before final patch warned at `94.6m` age | Added `source_driven` freshness mode and test coverage; final integrity report is clean | CLOSED |

## Verifiers

- Shadow log integrity: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `52` JSONL files, `55,586` JSONL rows.
- Live shadow data health: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `48/48` candidate coverage in all critical dependent logs.
- Forward capture readiness: `OK=12`, `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE_OR_NOT_YET_WIRED=1`.
- Follow-up coverage audit: all implemented live follow lanes accounted for; approval/source-trigger lanes remain explicit.
- Sierra forward inventory: `15` `READY_SCID_AND_DEPTH_PRESENT`, `3` `CAUTION_SCID_PRESENT_DEPTH_MISSING`.
- Watchdog E2E: `WARN`, not `FAIL`; only warning is owner-approved canary skip active until `2026-05-04T23:59:59+00:00`.

## External Data Status

Sierra:

- Process is running/responding.
- Forward inventory: `15` ready SCID+depth symbols, `3` SCID-only cautions.
- Candidate feature lane: `48/48` coverage.
- Full heavy extraction remains deferred for `24` rows; source path/mtime/size is already preserved.
- GBPJPY keeps `NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL` instead of inferred confluence.

Databento:

- Live confluence collector remains not enabled in the environment for this monitoring lane.
- Trigger-decision rows cover `48/48` candidates.
- `databento_live_confluence.jsonl` remains a waiting lane until a registered trigger and collector path are explicitly enabled.
- Paid fetch count: `0`.

## Open Limitations

- `SOURCE_NOT_CAPTURED` fields remain for structural-lock/FVG/V3 variants: `cost_aware_min_r_fields`, `fvg_lock_state`, `post_lock_reentry_state`, `standalone_fvg_entry_geometry`, `structural_lock_event_time_price`, and `swing_protected_lock_level`.
- These cannot be backfilled honestly from later candles. The rule remains: backfill only from original decision-time source rows/files that contain the exact value.
- Databento live confluence is waiting for an explicit registered trigger/collector/env path; do not poll every candle.
- GBPJPY has no registered direct Sierra proxy; rows must keep the blocker rather than infer 6B/6J confluence.
- `US30_cash` read-only tick probe returned null after KZ close; no positions/orders existed and US30 was outside active monitoring window, so this is not an open urgent issue.

## Completion Audit Verdict

The full 2026-05-04 live-monitoring objective is complete for the day. Core KZs closed, GER40 tier-2 shadow observation closed at `19:00 UTC`, no open positions/orders remain, final shadow readers are clean, critical data-capture gaps found during the day were fixed/backfilled from original evidence, and remaining gaps are explicit source/approval blockers rather than silent capture failures.

Do not treat this report as a strategy promotion or trading recommendation.
