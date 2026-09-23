# Expanded OOS FX/Silver Proxy Replay Registry - 2026-05-04

## Scope

- Status: REGISTERED BEFORE REPLAY.
- Research mode only.
- Promotion verdict: `NO_PROMOTION_VERDICT`.
- AI/API calls: not approved and not used.
- Databento calls: not used for this registry.
- Live trading logic, prompts, risk, execution, and safety gates: out of scope.

## Registered Proxy Pilots

| Batch | Family | Source | Replay Symbol | Evidence Class | Transform | Boundary |
|---|---|---|---|---|---|---|
| `sierra_6j_to_usdjpy_pilot_20260504` | USDJPY with 6J | `6JM26-CME` | `USDJPY` | `FUTURES_PROXY_TRANSFER` | `inverse` | Proxy caution; not broker-truth mapping. |
| `sierra_6b_to_gbpusd_pilot_20260504` | GBPUSD with 6B | `6BM26-CME` | `GBPUSD` | `FUTURES_PROXY_TRANSFER` | `identity` | Proxy-transfer diagnostic only. |
| `sierra_si_to_xagusd_pilot_20260504` | XAGUSD with SI | `SIM26-COMEX` | `XAGUSD` | `FUTURES_PROXY_TRANSFER` | `identity` | Sparse-source warning; proxy-transfer diagnostic only. |

## Conversion Contract

- Timeframes: M1, M5, M15, H1, D1.
- Conversion slice: full local SCID file for lookback availability.
- Replay opened slice: `2026-04-15T00:00:00Z` to `2026-04-17T17:00:00Z`.
- Holdout impact after run: burned only for these named proxy pilots.

## Interpretation Boundary

These pilots are adapter/replay-unblocking diagnostics. They can show whether the replay path handles the mapped source family, but they cannot validate broker execution truth, cannot certify proxy equivalence, and cannot promote any live rule.
