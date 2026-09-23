# Live Shadow L2 Interpretation - 2026-05-04

Status: active monitoring doctrine note
Promotion verdict: `NO_PROMOTION_VERDICT`

## Rule

L2 verification still applies to production candidates. It does not filter candidates out of the live-shadow/follow-data logs.

Current flow:

1. AI emits `CANDIDATE`.
2. L2 verification checks deterministic MSO/geometry facts.
3. Production path either continues toward execution or records `REJECTED_L2`.
4. The live-shadow logger records the candidate with `final_outcome_at_log`, full `verification`, and strategy snapshots.
5. Candidate path follow and mechanical shadow outcome rows continue observing price action after the decision.

## Why L2 Exists

L2 is a production safety and hallucination filter. It grounds the AI candidate against deterministic market-state facts before an order can be placed.

Examples of L2 checks:

- M15 CHoCH/BOS with displacement exists.
- Displacement ratio meets threshold.
- H1 POI/OB exists.
- OB is in the correct premium/discount zone.
- Entry lies inside the OB/FVG/breaker geometry.
- SL is beyond the relevant OB/FVG/breaker anchor.
- Gap/entry geometry is valid.

## How To Read Today's Shadow Evidence

For the 2026-05-04 London XAGUSD sequence, production records `REJECTED_L2` with `blocked_by=m15_choch_exists`. Shadow rows still follow those candidates and, as of the 09:45 UTC checkpoint, several reached TP1 or TP area.

Interpretation:

- This is evidence that the current L2 `m15_choch_exists` requirement may be too strict, instrument-specific, or regime-sensitive for this live slice.
- It is not evidence to remove L2 immediately.
- It is not a production trade result.
- It is valid forward-shadow evidence for later review of L2 strictness, limit-entry strictness, and market/proximity comparator behavior.

Future review should compare:

- production `REJECTED_L2` rows,
- shadow path outcome rows,
- mechanical strategy outcomes,
- M15 event availability at decision time,
- actual broker/fill truth,
- source-status blockers,
- and no-lookahead constraints.
