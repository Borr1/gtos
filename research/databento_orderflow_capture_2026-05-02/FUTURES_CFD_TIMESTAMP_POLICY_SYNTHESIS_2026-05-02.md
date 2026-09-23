# Futures-CFD Timestamp Policy Synthesis

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Can we remove the futures-to-CFD timestamp ambiguity without choosing a shift after seeing each window?

## Evidence

The timestamp policy audit reran CME futures to MT5 CFD mapping on seven windows:

| Window | Selected MT5 shift | Primary min abs corr | Read |
|---|---:|---:|---|
| 2026-01-15 | -120 | 0.9813 | UTC+2 broker timestamp |
| 2026-02-12 | -120 | 0.9722 | UTC+2 broker timestamp |
| 2026-03-06 13:30-15:30 | -120 | 0.9948 | still UTC+2 before US DST weekend |
| 2026-03-09 13:30-15:30 | -180 | 0.9907 | UTC+3 after US DST weekend |
| 2026-03-13 | -180 | 0.9833 | UTC+3 |
| 2026-04-02 | -180 | 0.9837 | UTC+3 |
| 2026-04-24 | -180 | 0.9693 | UTC+3 |

Source: `FUTURES_CFD_TIMESTAMP_POLICY_AUDIT_2026-05-02.md`.

## Synthesis

The timestamp ambiguity is now materially reduced. For the tested 2026 MT5 exports, the research-local policy should be:

- use `-120` minute MT5 shift before the March 2026 US DST transition,
- use `-180` minute MT5 shift after the March 2026 US DST transition,
- never infer the shift independently per event in alpha tests,
- record the applied shift beside every joined futures/CFD row.

This is consistent with the broker-export timestamps behaving like UTC+2 in winter and UTC+3 after the US DST weekend. The current evidence pins the observed transition between Friday 2026-03-06 and Monday 2026-03-09.

## What This Closes

- A fixed all-year `-180` shift is wrong for Jan-Feb 2026.
- A fixed all-year `-120` shift is wrong after 2026-03-09.
- Per-window best-shift selection is not acceptable for future alpha tests because it is a hindsight operation.

## Ambiguity Ledger

- The audit does not test November 2026 DST fallback because the current MT5 M1 export ends before that period.
- The exact broker-server timezone rule is inferred from price alignment, not read from broker metadata.
- Roll-date behavior remains untested.
- M1 alignment can hide sub-minute lag; tick-level validation remains pending.
- This validates transfer/timestamp handling only, not orderflow alpha.

## Open Questions

1. Does the same UTC+2/UTC+3 policy hold for future exports after the broker/server changes DST again?
2. Does tick-level alignment show the same transition without hidden sub-minute lag?
3. Do futures roll windows need separate mapping guards?

## Next Steps

1. Encode the timestamp policy in future research joins as a deterministic date-aware transform.
2. Add an audit field to future orderflow feature rows: `mt5_time_shift_minutes_applied`.
3. Re-run transfer validation on a futures roll window before using roll-adjacent events.
4. Re-check the policy after new MT5 M1 exports extend through the next DST transition.
