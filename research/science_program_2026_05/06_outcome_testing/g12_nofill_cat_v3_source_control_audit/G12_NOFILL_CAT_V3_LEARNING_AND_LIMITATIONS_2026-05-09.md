# G12 NOFILL CAT V3 Learning And Limitations - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.

## What V3 Proves

- The prior 298-row no-fill universe is represented exactly once.
- The V3 terminal families reconcile to 225 accepted input-only categorical rows, 4 source-control rows, 4 source-impossible rows, 0 unresolved blockers, and 65 rejects.
- May 3 rows 0049/0050/0051 are source-control market-session-empty evidence only.
- XAUUSD 0241 is source-control input-only no-entry-through-cancel evidence only.
- USDJPY rows 0130/0143/0165/0178 remain source-impossible from approved routes because the first decisive quote row simultaneously satisfies entry and protective predicates without a sub-row sequence source.

## What V3 Does Not Prove

- It does not score outcomes, R, win rate, expectancy, or validation lift.
- It does not inspect broker actual-R, account history, live order/deal/position labels, or hidden labels.
- It does not make any row validation-safe, promotable, or live-effective.
- It does not solve the USDJPY event-order question; it reduces it to an exact source requirement.

## Limitations

- Source-hash recomputation found two mutable context hash drifts and one line-ending-only prompt hash drift; no stable source-data hash mismatch was found.
- Exact USDJPY ordering remains externally blocked unless a broker-native quote-event sequence or sub-row/sub-millisecond source appears.
- A future result lane must be a separate evidence-class gate and must not reuse this audit as performance validation.
