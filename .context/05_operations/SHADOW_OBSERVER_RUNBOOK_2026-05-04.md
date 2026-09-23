# Shadow Observer Runbook - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

This runbook covers the separate no-AI, no-execution observer for instruments tested or mapped in research but not running as live GTOS orchestrators.

## Start

One read-only cycle:

```powershell
python scripts/run_shadow_observer.py --mode live --profile redacted_account --once
```

Continuous service:

```powershell
python scripts/run_shadow_observer.py --mode live --profile redacted_account
```

Optional symbol subset:

```powershell
python scripts/run_shadow_observer.py --mode live --profile redacted_account --symbols EURUSD,GER40
```

## What It Must Never Do

- no AI/API calls
- no canary calls
- no Databento calls
- no order placement
- no execution engine import
- no permission-gate invocation
- no outcome opening for preregistration-blocked lanes

## Current Active Lanes

Active MSO-only observers:

- `EURUSD` with broker symbol `EURUSD`, family `EURUSD/6E`
- `GER40` with broker symbol `GER30`, family `GER40 tier-2`
- `UK100` with broker symbol `UK100`, family `UK100 tier-2`

Blocked lanes retained in the registry for context:

- `ES/MES`: preregistration required before strategy/outcome cohort
- `CL`, `ZN`, `VIX/VXM`: context/control only
- `NZDUSD`: killed historical lane

## Logs To Monitor

- `shadow_logs/shadow_observer_status.jsonl`
- `shadow_logs/strategy_follow_evaluations.jsonl`
- `shadow_logs/shadow_observer_tick_enrichment.jsonl`
- `pipeline_state/shadow_observer_state.json`
- `knowledge_base/meta/.shadow_observer.lock`
- `logs/shadow_observer.log`

Expected status values include:

- `EMITTED_STRATEGY_FOLLOW_EVALUATION`
- `SKIPPED_OUTSIDE_KILL_ZONE`
- `SKIPPED_DUPLICATE_CANDLE`
- `BLOCKED_SYMBOL_NOT_READY`
- `BLOCKED_DATA_INCOMPLETE`
- `ERROR_FAIL_OPEN`

Every strategy row carries `source_run_id`, `dedupe_key`, `observer_metadata.observer_id`, `symbol`, `broker_symbol`, `source_symbol`, `decision_time_utc`, and `created_at_utc`. Do not aggregate these rows by symbol/time alone; use `dedupe_key` plus schema/source fields.

## Monitoring Cadence

- During active KZs for the registered observer symbols, status freshness should stay under 3600 seconds.
- EURUSD observer tick enrichment is maintained by the active follow pass: `python scripts/follow_live_candidate_paths.py --max-hours 12` invokes the duplicate-protected enrichment lane by default. Manual recovery remains available with `python scripts/backfill_shadow_observer_tick_enrichment.py --symbols EURUSD`.
- Outside KZ, `SKIPPED_OUTSIDE_KILL_ZONE` rows are normal.
- A strategy row should only appear once per observer per closed M15 candle.
- Repeated outside-KZ and duplicate-candle status rows are throttled to avoid log spam; use `logs/shadow_observer.log` for every-cycle liveness.

## Verifiers

```powershell
python scripts/verify_forward_capture_readiness.py
python scripts/audit_live_shadow_followup_coverage.py --output-json research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md
```

If rows are absent during an active KZ, check in this order:

1. `shadow_logs/shadow_observer_status.jsonl`
2. MT5 symbol visibility for broker symbols `EURUSD`, `GER30`, `UK100`
3. configured kill zones in `config/agent_config.yaml`
4. `logs/shadow_observer.log`
5. process list for `run_shadow_observer.py`

Do not "fix" missing rows by enabling ES/MES, CL/ZN/VIX, or NZDUSD. Those boundaries are research decisions, not runtime failures.
