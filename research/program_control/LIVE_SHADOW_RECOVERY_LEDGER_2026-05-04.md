# Live Shadow Recovery Ledger - 2026-05-04

**Schema:** `live_shadow_recovery_ledger_v1`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Scope:** shadow/follow-data repair only. No trading logic, prompt, risk, canary, AI, Databento, or order-path changes.

## Repairs

| Issue | Status | Evidence |
|---|---|---|
| D1 bias-lag JSONL fragments | Fixed with raw backup + quarantine | `shadow_logs/d1_bias_lag.jsonl` now has 333 valid rows; raw backup at `research/program_control/raw_shadow_log_quarantine/d1_bias_lag.jsonl.raw_20260504T080331Z_bc2a992877b0.bak`; fragments logged to `shadow_logs/d1_bias_lag_recovery.jsonl`. |
| Mechanical/V2/V3 rows missing independent follow outcomes | Fixed for explicit tracking | `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl` now has 288 rows across 6 candidates and 18 candidate/as-of snapshots. |
| EURUSD shadow observer tick enrichment missing | Fixed from MT5 recent ticks | `shadow_logs/shadow_observer_tick_enrichment.jsonl` has 5 EURUSD observer windows with `FEATURES_EXTRACTED`. |

## Mechanical Shadow Counts

| Score status | Rows |
|---|---:|
| `COMPUTED_FROM_CANDIDATE_PATH` | 72 |
| `NOT_AN_ENTRY_STRATEGY` | 36 |
| `MISSING_REQUIRED_LIVE_METADATA` | 144 |
| `NOT_COMPUTABLE` | 18 |
| `NOT_APPLICABLE` | 14 |
| `CONTEXT_ATTACHED` | 4 |

`MISSING_REQUIRED_LIVE_METADATA` is intentional and explicit: exact V2/V3 lock/reentry variants cannot be truthfully synthesized from today’s candidate rows alone. Those rows now preserve the gap per candidate instead of hiding it.

## Validation

- `python -m py_compile ...` passed for changed modules/scripts.
- Targeted pytest passed: `20 passed` for forward/mechanical/repair, then `9 passed` for observer enrichment/mechanical/repair.
- `python scripts/verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues=0`.
- `python scripts/verify_forward_capture_readiness.py`: `OK=12`, `WAITING=1`.
- `python scripts/_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0` at candle `2026-05-04T08:00:00+00:00`.
