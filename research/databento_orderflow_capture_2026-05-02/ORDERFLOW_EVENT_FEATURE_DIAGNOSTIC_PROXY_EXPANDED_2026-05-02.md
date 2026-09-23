# Orderflow Event Feature Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

Trades-level orderflow features were extracted for fetched GTOS event windows. This is a diagnostic feature table, not a trading rule or promotion claim.

## Coverage

- Feature rows: 324
- Primary ok rows: 237
- Data status counts: {'no_data': 4, 'ok': 320}

## Primary Proxy Medians By Event Class

| Event class | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate | 54 | 3.0000 | 0.4951 | 25.4499 | 0.6752 | 5.0000 | -2.0000 |
| m15_choch_context | 45 | -20.0000 | 0.4953 | 27.2458 | 0.6569 | 7.0000 | -4.0000 |
| structural_context | 138 | 4.0000 | 0.5013 | 31.4090 | 0.6729 | 6.5000 | 3.0000 |

## Primary Proxy Medians By Symbol

| Symbol | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |
|---|---:|---:|---:|---:|---:|---:|---:|
| GBPUSD | 44 | 7.0000 | 0.4921 | 88.5476 | 0.7868 | 4.0000 | -1.0000 |
| NAS100 | 73 | -33.0000 | 0.4974 | 45.2562 | 0.6719 | 27.0000 | -14.0000 |
| US30_cash | 83 | 9.0000 | 0.5046 | 27.2458 | 0.5714 | 5.0000 | 4.0000 |
| XAGUSD | 14 | -5.0000 | 0.4769 | 9.0517 | 0.5665 | 2.0000 | 7.0000 |
| XAUUSD | 23 | -8.0000 | 0.4853 | 13.6806 | 0.7414 | 10.0000 | -10.0000 |

## Ambiguity Ledger

- Trade side is Databento aggressor-side metadata; it is not identical to full footprint bid/ask-depth reconstruction.
- Zero-record weekend windows are retained as no_data and excluded from primary feature medians.
- Candidate-vs-context medians are descriptive only; no outcome edge or significance is claimed.
- Post-event features are for forensic diagnostics and must not be used in any future as-of decision rule.
- Depth/heatmap concepts such as resting liquidity and queue absorption remain untested by trades schema.

## Open Questions

1. Do pre-event features alone separate candidates from structural context once outcomes are joined?
2. Are LVN/POC proximity features stable across symbols or dominated by one instrument/session?
3. Which candidate windows deserve mbp-1/mbp-10 depth pulls for true resting-liquidity validation?
4. Do post-event diagnostics show trap/rejection patterns that can be re-expressed as pre-event hypotheses?

## Next Steps

1. Join feature rows to synthetic/actual R outcomes and keep post-event fields out of as-of candidate hypotheses.
2. Run candidate-versus-context and winner-versus-loser diagnostics on pre-event features only.
3. Register a small number of structural orderflow hypotheses before any replay-style test.
4. Spend depth credits only on the subset of windows where trades-level diagnostics show a coherent mechanism.
