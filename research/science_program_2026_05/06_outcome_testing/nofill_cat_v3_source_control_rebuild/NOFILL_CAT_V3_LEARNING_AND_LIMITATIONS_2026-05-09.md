# NOFILL CAT V3 Learning And Limitations - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.

## What V3 Proves

- The full prior 298-row V2 no-fill categorical universe can be represented exactly once with terminal source-control states.
- The prior 225 accepted input-only categorical rows can be carried forward unchanged.
- XAUUSD 0241 has G12-accepted source-control input-only evidence that no side-aware short entry touch occurred before cancel.
- May 3 rows 0049/0050/0051 have G12-accepted market-session-empty source-control evidence.
- USDJPY rows 0130/0143/0165/0178 are source-impossible from approved routes until a broker-native quote-event sequence source appears.
- The 65 rejects remain excluded.

## What V3 Does Not Prove

- It does not score any outcome or move any row into validation.
- It does not support a promotion or live trading change.
- It does not prove a USDJPY lifecycle result for the source-impossible rows.
- It does not turn source-control rows into accepted denominator rows.

## Strongest Counterargument Tested

The strongest counterargument is that consuming XAUUSD 0241 or May 3 source-control evidence could silently change the accepted denominator or mix source-control facts with lifecycle/result labels. V3 tests this by assigning those rows to explicit non-denominator `source_control` terminal states, checking accepted denominator count remains 225, and verifying all source-control/impossible/reject rows have no categorical label assignment.

## Future Source/Telemetry Routes

- Add a broker-native quote-event sequence capture if the platform exposes one; otherwise preserve USDJPY same-tick impossibility.
- Preserve source-control terminal states as packet hygiene for future G12 review.
- Keep result-contract changes behind a separate evidence-class gate.
