# GTOS Active Monitoring Checkpoint - 2026-05-04 10:41 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: live system health, NAS100 recovery, live-shadow/follow-data integrity

## System Health

- Local check time: `2026-05-04T18:41:xx+08:00`.
- Latest monitor candle: `2026-05-04T10:30:00+00:00`.
- `scripts\_live_monitor_iter.py` at `10:34 UTC`: `crit=0`, `anom=0`, `pids=6`, `open_pos=0`.
- MT5 read-only check: initialized, `last_error=[1,"Success"]`, `orders=[]`, `positions=[]`.
- NAS100 heartbeat had stopped at `2026-05-04T10:29:05.311948+00:00`, while other six orchestrators were fresh and NAS100 tick capture remained fresh.
- NAS100 log stopped after the `10:30` candidate/shadow-DA warning; the process was alive briefly but stopped writing heartbeat. Classification: `SERIOUS` live-observe orchestrator heartbeat stall outside active NAS100 KZ.
- Action: restarted only NAS100 after confirming no broker orders/positions. The first sandbox-local background start did not persist; the successful restart was launched outside the sandbox so it remained alive.
- Recovery evidence: NAS100 lock `pid=7312`, started `2026-05-04T10:38:17.577447+00:00`; heartbeat `2026-05-04T10:41:17.892629+00:00`; bootstrap log shows MT5 connected, account balance read, and ready state.
- Post-recovery `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No canary subprocess was spawned by the restart; the active owner-approved canary-skip marker remains valid through `2026-05-04T23:59:59+00:00`.

## Shadow Follow And Integrity

At `10:38 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=17`
- `candidate_path_follow.jsonl`: `1` new row
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `16` new rows, `2000` seen
- Gap-closure rows advanced: account truth `1`, LTF path `1`, Databento trigger `1`, FVG/OB resolutions `1`, rollups `1`, structural metadata `1`, missed-opportunity `1`, pre-fill resolutions `1`, Sierra status `1`, V2b resolutions `1`
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

The first integrity pass at `10:38 UTC` found `MODERATE=3` freshness warnings for:

- `proxy_blocker_status.jsonl`
- `ml_shadow_status.jsonl`
- `external_source_blocker_status.jsonl`

Root cause: these blocker ledgers were intended as status/control heartbeats, but their row keys were static, so append-only duplicate protection prevented freshness updates after the first write.

Fix shipped in working tree:

- `src\research_infra\live_shadow_gap_closure.py` now keys blocker/status rows by a 15-minute `status_bucket_utc`.
- `tests\test_live_shadow_gap_closure.py` adds regression coverage proving rows deduplicate within a bucket and refresh on the next bucket.
- Validation:
  - `python -m py_compile src\research_infra\live_shadow_gap_closure.py scripts\follow_live_candidate_paths.py` passed.
  - Escalated pytest, due Windows temp permissions: `python -m pytest tests\test_live_shadow_gap_closure.py tests\test_follow_live_candidate_paths.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_gap_closure_blocker_status_escalated` -> `9 passed`.
- Backfill/current-bucket follow pass at `10:41 UTC` wrote blocker rows: external source `6`, ML status `1`, proxy blocker `1`.
- Final `scripts\verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, JSONL rows inspected `25647`.

## Production Versus Shadow Snapshot

Production as of `10:41 UTC`:

- Open broker orders: `0`.
- Open broker positions: `0`.
- XAGUSD `10:00`, `10:15`, and `10:30`: production path `REJECTED_GATE1_SAFETY`; L2 passed, then Gate1 touch-count safety rejected.
- NAS100 `10:30`: production path `REJECTED_GATE1_SAFETY`; L2 passed, then deterministic safety blocked; no broker order.

Shadow/path outcomes as of `10:41 UTC`:

- Total followed candidates: `17`.
- Latest NAS100 `10:30` shadow path: `ENTRY_TOUCHED_THEN_SL` for a SHORT candidate with entry `27736.8`, TP1 `27674.6`; this is shadow-only evidence because production rejected the candidate before execution.
- Recent XAGUSD `09:45` through `10:30` rows remain `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`.
- Mechanical-shadow rows are current to `2000` rows; blocker/status rows are current and no longer stale.

## Known Boundaries

- `databento_live_confluence.jsonl`, BE, partial-close, time-in-trade, and `ml_shadow_predictions.jsonl` remain documented waiting/approval/paid-data lanes.
- Each candidate rollup still has unresolved structural/FVG-lock strategy variants where exact decision-time source fields are not present.
- Shadow results are observational only and do not imply live trade permission or promotion.

## Next Monitoring Action

Continue monitoring cadence. GBPUSD London observer window remains active until `12:00 UTC`; NY KZ starts later at `13:00 UTC` for XAUUSD/USDJPY/GBPJPY/GBPUSD/NAS100 and `13:30 UTC` for US30.
