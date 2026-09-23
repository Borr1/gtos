# Orderflow MBP-10 Ladder Feature Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

Sampled MBP-10 ladder-depth features were extracted for scoped candidate windows across current primary futures proxies. This tests whether deeper book state opens a defensible next hypothesis.

## Coverage

- Feature rows: 59
- Data status counts: {'ok': 59}
- Sample method: one_second_last_quote_per_symbol
- Depth scope: top_10_levels

## Readout

- GBPUSD MBP-10 outcome rows are one-sided or sparse: winner n=9, loser n=0; no GBPUSD ladder claim can be made.
- XAUUSD MBP-10 outcome rows are one-sided or sparse: winner n=2, loser n=0; no XAUUSD ladder claim can be made.
- NAS100 MBP-10 outcome rows remain failure-cluster dominated: winner n=1, loser n=10.
- NAS100 winner-minus-loser ladder deltas: depth10 imbalance=-0.0135, thin-rate=-0.1693, total-depth=34.0000.
- MBP-10 answers more of the ladder question than MBP-1, but this sampled pilot is not promotion-grade.

## Candidate vs Context

| Symbol | candidate n | context n | depth10 imbalance delta | thin-rate delta | total-depth delta | near/far delta | max bid wall delta | max ask wall delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GBPUSD | 21 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| NAS100 | 12 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| US30_cash | 1 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| XAGUSD | 14 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| XAUUSD | 10 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |

## Outcome By Symbol

| Symbol | winner n | loser n | depth10 imbalance W-L | thin-rate W-L | total-depth W-L | near/far W-L | max bid wall W-L | max ask wall W-L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GBPUSD | 9 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| NAS100 | 1 | 10 | -0.0135 | -0.1693 | 34.0000 | 0.0152 | 2.0000 | 2.0000 |
| XAUUSD | 2 | 0 | n/a | n/a | n/a | n/a | n/a | n/a |

## Ambiguity Ledger

- This uses one-second last-quote snapshots, so it does not capture every queue addition/cancellation or intra-second spoof/cancel pattern.
- MBP-10 gives the top 10 levels, not full MBO order identity or queue position.
- The sample is selected from known interesting windows and is not population-random.
- Actual broker realized-R coverage remains too sparse; outcome rows are mostly synthetic/path labels.
- No depth thresholds were optimized, registered, or promoted.

## Open Questions

1. Does any symbol-specific failure cluster show a repeatable ladder-depth signature in future windows?
2. Is the observed ladder state a cause of failure or just a byproduct of the same structural regime?
3. Would MBO add materially more than MBP-10 for our purposes, or is the storage/cost burden unjustified?
4. Can ladder-thinness or depth imbalance be turned into a single pre-registered hypothesis with fixed windows and no threshold mining?

## Next Steps

1. Do not buy broad MBP-10/MBO history yet; wait for more candidate outcomes or a precise hypothesis.
2. Use MBP-10 only for targeted forensic windows until actual-R coverage improves.
3. If a hypothesis is registered, freeze the feature family, lookback window, and threshold before replay.
4. Forward-collect candidate windows with trades + MBP-1 by default, and promote MBP-10 collection only when a candidate enters a high-value forensic bucket.
