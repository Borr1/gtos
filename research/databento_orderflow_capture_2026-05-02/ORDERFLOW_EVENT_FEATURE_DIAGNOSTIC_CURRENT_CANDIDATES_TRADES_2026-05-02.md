# Orderflow Event Feature Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

Trades-level orderflow features were extracted for fetched GTOS event windows. This is a diagnostic feature table, not a trading rule or promotion claim.

## Coverage

- Feature rows: 59
- Primary ok rows: 58
- Data status counts: {'ok': 59}

## Primary Proxy Medians By Event Class

| Event class | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate | 58 | 3.0000 | 0.4951 | 22.3129 | 0.6569 | 5.0000 | -2.0000 |

## Primary Proxy Medians By Symbol

| Symbol | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |
|---|---:|---:|---:|---:|---:|---:|---:|
| GBPUSD | 21 | 17.0000 | 0.5085 | 107.0000 | 0.6923 | 4.0000 | -1.0000 |
| NAS100 | 12 | -28.0000 | 0.4929 | 17.6063 | 0.5821 | 21.5000 | -35.5000 |
| US30_cash | 1 | -191.0000 | 0.4631 | 47.0727 | 0.3867 | 7.0000 | 114.0000 |
| XAGUSD | 14 | 5.5000 | 0.4901 | 8.6847 | 0.6162 | 2.5000 | 3.5000 |
| XAUUSD | 10 | 13.0000 | 0.5015 | 18.4438 | 0.7298 | 8.5000 | -8.0000 |

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
