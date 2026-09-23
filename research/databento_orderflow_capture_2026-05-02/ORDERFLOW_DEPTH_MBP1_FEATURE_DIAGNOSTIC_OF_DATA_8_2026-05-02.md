# Orderflow MBP-1 Depth Feature Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

MBP-1 top-of-book depth features were extracted for the scoped XAUUSD/NAS100 pilot windows. This is a spend-controlled diagnostic, not a trading rule.

## Coverage

- Feature rows: 45
- Data status counts: {'ok': 45}
- Limitation: top_of_book_only

## Readout

- NAS100 MBP-1 outcome rows are still failure-cluster dominated: winner n=1, loser n=10.
- XAUUSD MBP-1 outcome rows have winner n=2 and loser n=0; no XAUUSD depth rule can be inferred.
- NAS100: candidate/context n=11/32, event15 imbalance delta=0.0000, event15 thin-rate delta=0.0093.
- MBP-1 can support top-of-book diagnostics, but it cannot validate full footprint/heatmap claims.
- No promotion or parameter change is justified from this pilot.

## Candidate vs Context

| Symbol | candidate n | context n | event15 imbalance delta | event15 thin-rate delta | event15 spread delta | pre60 top liquidity delta |
|---|---:|---:|---:|---:|---:|---:|
| NAS100 | 11 | 32 | 0.0000 | 0.0093 | 0.0000 | -1.5000 |
| XAUUSD | 2 | 0 | n/a | n/a | n/a | n/a |

## Outcome By Symbol

| Symbol | winner n | loser n | event15 imbalance W-L | event15 thin-rate W-L | event15 spread W-L | pre60 top liquidity W-L |
|---|---:|---:|---:|---:|---:|---:|
| NAS100 | 1 | 10 | 0.0000 | -0.0494 | 0.0000 | 1.0000 |
| XAUUSD | 2 | 0 | n/a | n/a | n/a | n/a |

## Ambiguity Ledger

- MBP-1 only gives best bid/ask depth; it does not reconstruct the full ladder, LVN/HVN heatmap, queue position, or iceberg behavior.
- The sample was selected from already-interesting windows, so candidate/context differences are diagnostic and not a population claim.
- Outcome labels remain mostly synthetic/path labels; broker actual-R coverage is still too sparse.
- Top-of-book imbalance can be quote-noisy and may reflect liquidity provision/cancellation rather than executed intent.
- No thresholds were optimized or registered in this pilot.

## Open Questions

1. Does NAS100 failure-cluster depth separation persist after more live candidate windows accrue?
2. Would MBP-10 or MBO expose ladder-level LVN/liquidity-pocket behavior that MBP-1 cannot see?
3. Can top-of-book thinness/imbalance be transformed into a pre-registered structural hypothesis without post-hoc thresholding?
4. Do XAUUSD winner-like rows share a distinct depth signature once enough non-winner examples exist?

## Next Steps

1. Use this MBP-1 pilot to decide whether a deeper MBP-10/MBO pull is worth spending on only the NAS100 failure cluster.
2. Keep depth features separate from trades-level footprint features until a registered hypothesis is written.
3. Do not spend on broad depth history until candidate/outcome coverage expands.
4. Forward-collect executed-trade actual R so depth diagnostics can eventually be scored against broker outcomes.
