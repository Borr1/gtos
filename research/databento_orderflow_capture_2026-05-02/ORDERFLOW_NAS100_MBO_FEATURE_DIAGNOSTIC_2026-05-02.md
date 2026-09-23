# NAS100 MBO Feature Diagnostic

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registered hypothesis: `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1`

## Summary

Registered NAS100/NQ MBO diagnostics were extracted from UTC-midnight MBO pulls. Only pre60 and event15 as-of windows are scored.

## Coverage

- Feature rows: 59
- Data status counts: {'ok': 59}
- Decision windows: ['pre60', 'event15']
- Forbidden windows: ['post15', 'post60']

## Readout

- NAS100 MBO candidate/context n=12/47; event15 total-depth20 delta=-33.5000, pull-pressure delta=0.0023, net-liquidity delta=115.0000.
- NAS100 MBO outcome n winner/loser=1/10; winner-minus-loser pull-pressure=-0.0081, winner-minus-loser total-depth20=68.5000.
- This is a registered diagnostic pass, not a promotion result; actual broker-R coverage remains sparse.

## Candidate vs Context

| Bucket | n | event15 depth20 imbalance | event15 total depth20 | event15 thin rate | event15 wall concentration | event15 pull pressure | event15 net liquidity |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate | 12 | -0.0093 | 117.5000 | 0.1471 | 0.0588 | 0.5047 | -681.0000 |
| context | 47 | -0.0319 | 151.0000 | 0.1956 | 0.0573 | 0.5024 | -796.0000 |
| candidate-context |  | 0.0226 | -33.5000 | -0.0485 | 0.0015 | 0.0023 | 115.0000 |

## Outcome Contrast

| Bucket | n | event15 depth20 imbalance | event15 total depth20 | event15 thin rate | event15 wall concentration | event15 pull pressure | event15 net liquidity |
|---|---:|---:|---:|---:|---:|---:|---:|
| winner | 1 | -0.0558 | 186.0000 | 0.0133 | 0.0583 | 0.4965 | 6389.0000 |
| loser | 10 | -0.0046 | 117.5000 | 0.1471 | 0.0600 | 0.5047 | -681.0000 |
| winner-loser |  | -0.0513 | 68.5000 | -0.1337 | -0.0017 | -0.0081 | 7070.0000 |

## Ambiguity Ledger

- MBO action semantics are normalized defensively; action-level add/remove/fill buckets should be cross-checked before any future promotion dossier.
- The current outcome contrast is dominated by synthetic/path labels, not broker actual R.
- Candidate dates were chosen because candidates already existed; this is registered diagnostic validation, not broad population inference.
- No threshold was fitted or selected from the MBO outcome readout.

## Open Questions

1. Does MBO add a clearer NAS100 failure signature than MBP-10?
2. Are near-touch pull/add pressure features stable enough to justify SierraChart full-depth capture?
3. Can future NAS100 candidates add enough winner-side coverage to test outcome contrast honestly?

## Next Steps

1. Compare this MBO readout against the MBP-10 result before deciding whether more Databento MBO spend is justified.
2. Continue forward surgical trades + MBP-10 collection for new NAS100 candidates.
3. Use SierraChart/full-depth only if the feature family remains coherent after this MBO pass.
