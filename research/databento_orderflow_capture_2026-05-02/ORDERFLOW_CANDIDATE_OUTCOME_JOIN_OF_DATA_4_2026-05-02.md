# Orderflow Candidate Outcome Join

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

Primary-proxy candidate orderflow features were joined to available candidate synthetic/actual outcomes. This is a small diagnostic join, not an alpha test or promotion claim.

## Coverage

- Candidate feature rows: 23
- Join matched: 14
- Target available: 13
- Winner / loser: 3 / 10
- Status counts: {'join_matched_no_target': 1, 'join_missing': 9, 'target_available': 13}

## Winner vs Loser As-Of Medians

| Feature | Winners | Losers |
|---|---:|---:|
| pre60_signed_volume | 1012.0000 | -94.5000 |
| pre60_buy_fraction | 0.5086 | 0.4933 |
| pre60_absorption_volume_per_tick | 36.7109 | 40.6826 |
| event15_signed_volume | -487.0000 | -28.0000 |
| event15_buy_fraction | 0.4758 | 0.4929 |
| event15_absorption_volume_per_tick | 18.8251 | 17.6063 |
| profile_event_price_volume_percentile | 0.7492 | 0.6616 |
| profile_nearest_lvn_distance_ticks | 7.0000 | 21.5000 |

## Readout

- Outcome-joined target count is 13; this is below promotion-grade sample size.
- Target coverage by symbol: {'NAS100': {'n': 11, 'wins': 1, 'losses': 10, 'mean_r': -0.7727}, 'XAUUSD': {'n': 2, 'wins': 2, 'losses': 0, 'mean_r': 1.5}}.
- The clearest current signal is a NAS100 candidate failure cluster, not a universal orderflow edge.
- XAUUSD looks positive in this join, but n is too small to generalize.
- Any next hypothesis should be symbol-stratified and as-of only.

## By Symbol

| Symbol | n | wins | losses | mean synthetic R | win rate | event15 signed vol | event15 buy fraction | profile percentile | nearest LVN ticks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NAS100 | 11 | 1 | 10 | -0.7727 | 0.0909 | -30.0000 | 0.4913 | 0.5835 | 16.0000 |
| XAUUSD | 2 | 2 | 0 | 1.5000 | 1.0000 | -50.5000 | 0.4816 | 0.7756 | 20.5000 |

## Ambiguity Ledger

- Synthetic realized R is not the same as broker actual realized R; actual realized coverage remains sparse.
- Only primary futures proxies are used in the outcome readout; ES remains a US30 comparator.
- The sample is recent live/shadow candidate coverage, not a historical population replay.
- Winner/loser feature medians are descriptive and not DSR/PBO/effective_N validated.
- Post-event features are deliberately excluded from this as-of outcome readout.

## Open Questions

1. Do any as-of orderflow features retain separation after symbol/session stratification?
2. Is apparent separation mostly a NAS100 failure signature rather than a universal orderflow mechanism?
3. Can actual realized-R coverage be enriched enough to replace synthetic labels?
4. Which one or two structural hypotheses deserve registration for a controlled replay?

## Next Steps

1. Run a symbol-stratified candidate diagnostic on as-of features only.
2. Treat NAS100 separately before forming any broad orderflow rule.
3. Backfill or forward-collect actual realized outcomes for these event rows.
4. If a hypothesis is registered, freeze thresholds before any replay-style evaluation.
