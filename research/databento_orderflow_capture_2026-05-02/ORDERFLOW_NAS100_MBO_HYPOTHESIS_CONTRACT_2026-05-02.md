# NAS100 MBO Hypothesis Contract

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Registered Hypothesis

Hypothesis ID: `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1`

Registered status: `REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE`

Question:

Do NAS100 GTOS CANDIDATE rows show pre-entry adverse-selection depth behavior in NQ full-depth MBO that is not fully answered by the prior MBP-10 diagnostic?

## Frozen Scope

- GTOS symbol: `NAS100`
- Futures proxy: `NQ.v.0`
- Event source: `ORDERFLOW_EVENT_WINDOW_MANIFEST_PROXY_EXPANDED_2026-05-02.json`
- Included event dates: NAS100 dates with at least one GTOS `candidate` event.
- Included event classes: `candidate`, `m15_choch_context`, and `structural_context` on those candidate dates.
- Raw MBO request policy: each included date starts at `00:00:00Z` for Databento synthetic book reconstruction.
- Feature windows: `pre60` and `event15` only.
- Forbidden decision inputs: `post15`, `post60`, future outcome path, future fills, and any threshold selected after seeing MBO outcomes.

## Frozen Labels

Labels must remain separated:

- synthetic/path R,
- broker actual R,
- fill/no-fill or limit-intent state.

Current primary diagnostic label is synthetic/path R because actual broker-R coverage is sparse. Any report must state that limitation before outcome interpretation.

## Frozen Feature Families

The extractor may compute descriptive rows, but the readout is restricted to these pre-declared families:

1. Full-depth state from reconstructed MBO book:
   - top-10 and top-20 total depth,
   - top-10 and top-20 bid/ask imbalance,
   - near/far ratio using top 5 vs levels 6-20,
   - max wall size within top 20,
   - wall concentration within top 20,
   - thin-depth rate using each event's own pre60 20th-percentile top-20 depth threshold.

2. Near-touch queue-flow behavior:
   - add size within 10 ticks of best bid/ask,
   - remove/cancel/fill size within 10 ticks of best bid/ask,
   - net near-touch liquidity add-minus-remove,
   - pull pressure: near-touch remove / (near-touch add + remove),
   - bid-side and ask-side pull pressure.

3. Price-state context:
   - mid change in ticks within the same as-of window.

No optimized threshold is registered here. The only fixed structural threshold is `near10` ticks from touch because it is a mechanical neighborhood definition, not an outcome-fitted cutoff.

## Evaluation Readout

Report these comparisons:

- NAS100 candidate vs same-date NAS100 context.
- NAS100 synthetic/path winners vs losers, with one-sided/sparse cohorts explicitly flagged.
- MBO readout versus prior MBP-10 readout.

Do not pool symbols. Do not claim universal orderflow alpha. Do not promote live behavior.

## Stop/Go Interpretation

This pass can produce only one of these research conclusions:

- `MBO_ADDS_COHERENT_DIAGNOSTIC_SIGNAL`: MBO has directional candidate/context or failure-cluster structure worth forward collection and SierraChart replication.
- `MBO_DOES_NOT_ADD_OVER_MBP10`: MBO does not improve clarity enough to justify near-term MBO spend.
- `MBO_UNEVALUABLE_LABEL_LIMITED`: extraction works, but winner/actual-R coverage is too sparse for outcome contrast.
- `MBO_TOOLING_BLOCKED`: raw schema or processing limitations prevent a trustworthy readout.

None of those outcomes is a promotion verdict.

## Ambiguity Ledger

- Databento MBO action semantics need defensive handling and later cross-checking before any promotion dossier.
- Starting at UTC midnight consumes raw data before the first candidate; this is required for book reconstruction, not exploratory dead-time mining.
- Current outcome contrast is synthetic/path-heavy and winner-side sparse.
- SierraChart/full-depth becomes justified only if this MBO feature family shows coherent diagnostic value or if Databento proves the same feature family is feasible but inconvenient to keep buying.

## Next Steps

1. Build the UTC-midnight NAS100/NQ MBO manifest.
2. Estimate cost before execution.
3. Fetch only the registered groups if the cap passes.
4. Run the MBO extractor on `pre60` and `event15`.
5. Write a synthesis that either keeps, narrows, or rejects this MBO lane.
