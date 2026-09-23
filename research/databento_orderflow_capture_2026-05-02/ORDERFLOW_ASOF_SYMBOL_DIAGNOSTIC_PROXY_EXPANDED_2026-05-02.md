# Orderflow As-Of Symbol Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This report isolates as-of orderflow features by symbol. It separates candidate-vs-context diagnostics from outcome-joined winner-vs-loser diagnostics.

## Readout

- NAS100 remains the only outcome-joined symbol with enough rows for a useful failure-cluster readout, but winner n=1 and loser n=10 are still too small for inference.
- XAUUSD has winner n=2 and loser n=0; it cannot validate an orderflow rule yet.
- GBPUSD has winner n=9 and loser n=0; it adds coverage but not winner/loser contrast.
- GBPUSD: candidate-vs-context n=21/23, profile-percentile delta=-0.1538, LVN-distance delta=1.0000.
- NAS100: candidate-vs-context n=12/61, profile-percentile delta=-0.0913, LVN-distance delta=-10.5000.
- US30_cash: candidate-vs-context n=1/82, profile-percentile delta=-0.1969, LVN-distance delta=2.0000.
- XAGUSD: candidate-vs-context n=10/4, profile-percentile delta=0.2445, LVN-distance delta=0.5000.
- XAUUSD: candidate-vs-context n=10/13, profile-percentile delta=-0.0502, LVN-distance delta=-4.5000.
- No broad rule is justified; next hypothesis must be symbol-stratified and pre-registered.

## Candidate vs Context By Symbol

| Symbol | candidate n | context n | profile percentile delta | nearest LVN ticks delta | event15 signed vol delta | event15 divergence-rate delta |
|---|---:|---:|---:|---:|---:|---:|
| GBPUSD | 21 | 23 | -0.1538 | 1.0000 | 37.0000 | -0.0580 |
| NAS100 | 12 | 61 | -0.0913 | -10.5000 | 12.0000 | -0.2609 |
| US30_cash | 1 | 82 | -0.1969 | 2.0000 | -201.0000 | 0.6707 |
| XAGUSD | 10 | 4 | 0.2445 | 0.5000 | 37.0000 | 0.2500 |
| XAUUSD | 10 | 13 | -0.0502 | -4.5000 | 31.0000 | -0.2846 |

## Outcome By Symbol

| Symbol | winner n | loser n | profile percentile W-L | nearest LVN ticks W-L | pre60 signed vol W-L | event15 signed vol W-L |
|---|---:|---:|---:|---:|---:|---:|
| GBPUSD | 9 | 0 | n/a | n/a | n/a | n/a |
| NAS100 | 1 | 10 | -0.3208 | -17.5000 | -2264.5000 | -1427.0000 |
| XAUUSD | 2 | 0 | n/a | n/a | n/a | n/a |

## Ambiguity Ledger

- Candidate outcomes are mostly synthetic; actual realized-R remains sparse.
- Feature thresholds are not optimized or promoted here.
- Outcome interpretation requires both winner and loser contrast inside a symbol; all-winner or all-loser symbols are not rule evidence.
- XAUUSD outcome coverage is too small to interpret as a continuation-quality rule.
- Context rows are structural/no-trade contexts, not randomized market rows.

## Open Questions

1. Does NAS100 failure separation persist after more candidate outcomes accrue?
2. Are profile percentile and LVN distance meaningful or just session/instrument artifacts?
3. Can actual realized-R enrichment replace synthetic labels for this diagnostic?
4. Which as-of feature family should be registered first: delta failure, LVN/POC location, or absorption?

## Next Steps

1. Register one NAS100 failure-filter hypothesis with frozen thresholds only after expanding n.
2. Backfill/forward-collect more XAUUSD and US30 candidate outcomes before symbol claims.
3. Run a depth-schema pilot only on the NAS100/XAUUSD candidate windows selected by this report.
