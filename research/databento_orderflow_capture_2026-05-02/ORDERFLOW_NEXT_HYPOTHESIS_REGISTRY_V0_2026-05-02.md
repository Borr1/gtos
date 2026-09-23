# Orderflow Next Hypothesis Registry V0

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Registry Status

One diagnostic orderflow hypothesis is now registered:

- `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1`

This is a diagnostic MBO validation registration, not a replay promotion, not a live-trading rule, and not a thresholded decision policy.

## Registered H1: NAS100 Failure-Filter / Adverse-Selection Depth

Status: `REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE`

Contract:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_HYPOTHESIS_CONTRACT_2026-05-02.md`

Scope:

- Symbol: NAS100 only.
- Event type: GTOS CANDIDATE rows only.
- Label: synthetic/path outcome until actual-R coverage improves.
- Data: trades + MBP-10 as prior diagnostics; NQ MBO full-depth as the next registered diagnostic.
- Decision windows: `pre60` and `event15` only.
- Raw MBO request policy: UTC-midnight-start daily pulls on candidate dates for synthetic book reconstruction.

Observation motivating it:

- Current NAS100 orderflow subset has winner/loser coverage of `1/10`.
- Expanded MBP-10 sampled ladder diagnostics show candidate/context event15 total-depth delta `-20.0000`.
- Winner-minus-loser total-depth delta is `34.0000`, but winner n is only `1`.

Frozen before MBO diagnostic:

- Exact candidate inclusion rules.
- Exact as-of windows.
- Exact feature family.
- Treatment of pre-execution rejects versus actual executed trades.
- Stop/go interpretation language.

Blocking ambiguity:

- Current winner n is too small.
- Actual broker R is only `1/23` in the orderflow candidate subset.
- The pilot windows were selected after trades diagnostics, so they are not population-random.
- MBO action semantics need defensive implementation and later cross-check before any promotion dossier.

## Candidate H2: XAUUSD Continuation Quality

Status: `CANDIDATE_NOT_REGISTERED`

Scope:

- Symbol: XAUUSD only.
- Event type: GTOS CANDIDATE rows only.
- Label: synthetic/path label until broker actual-R coverage exists.
- Data: trades first; MBP-1/MBP-10 only for selected rows.

Observation motivating it:

- XAUUSD current orderflow outcome rows are `2` synthetic winners and `0` synthetic losers.
- Futures-to-CFD mapping for gold is conceptually strongest because XAUUSD is directly tied to COMEX gold plus broker basis/spread.

Blocking ambiguity:

- There is no loser contrast.
- One XAUUSD `LIMIT_PLACED` row lacks execution/exit payload.
- No conclusion can be made until more XAUUSD candidate outcomes exist.

## Candidate H3: Limit-Fill / Execution-Awareness

Status: `CANDIDATE_NOT_REGISTERED`

Scope:

- Rows where GTOS emits `LIMIT_PLACED`.
- Label: fill/no-fill, broker actual R, timeout, adverse excursion.
- Data: trades + MBP-1 by default; MBP-10 for high-value forensic rows.

Observation motivating it:

- Orderflow may be more useful for fill quality and adverse selection than for deciding CANDIDATE versus NO_TRADE.
- Current actual-R bottleneck is an execution-label problem, not just a market-state problem.

Blocking ambiguity:

- Need broker-history reconciliation and forward actual-R collection.
- Need clear separation between unfilled limit intent and filled executed trade.

## Candidate H4: MBO Queue Behavior

Status: `DEFERRED_NOT_REGISTERED`

Scope:

- Only rows where MBP-10 diagnostics suggest ladder behavior matters but cannot explain the outcome.

Observation motivating it:

- Influencer-style footprint/heatmap language often implies queue behavior, absorption, and liquidity withdrawal.
- MBP-10 does not reveal order identity or queue position.

Blocking ambiguity:

- No current evidence proves MBO would add enough signal to justify broad cost/storage.
- MBO should not be pulled until H1/H3 produce a precise question MBP-10 cannot answer.

## Registration Rule

A future hypothesis may be registered only when:

1. Scope is symbol-specific.
2. Inputs are as-of only.
3. Feature family is named before replay.
4. Threshold derivation is frozen before replay.
5. Outcome label type is explicit: synthetic/path, actual broker R, or fill/no-fill.
6. Sample-size stop/go criteria are written before evaluation.
7. The report keeps `NO_PROMOTION_VERDICT` unless all methodology gates pass.
