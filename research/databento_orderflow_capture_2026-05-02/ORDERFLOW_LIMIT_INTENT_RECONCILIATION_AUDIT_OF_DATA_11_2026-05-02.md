# Orderflow Limit Intent Reconciliation Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This audit reconciles LIMIT_PLACED orderflow rows with missing actual R by separating internal GTOS limit intent, broker execution evidence, local logs, and M1 counterfactual path.

## Counts

- Limit rows audited: 1
- Reconciliation classes: {'discarded_internal_intent_but_research_path_would_have_filled': 1}
- Symbol counts: {'XAUUSD': 1}
- Broker actual-R rows: 0
- Limit-filled log rows: 0
- Pending-discard log rows: 1
- Counterfactual M1 TP rows: 1

## Readout

- Audited 1 LIMIT_PLACED orderflow rows with missing realized R.
- Broker actual-R rows recovered from local records: 0.
- Rows with LIMIT_FILLED log evidence: 0; rows with next-day pending-intent discard evidence: 1.
- 1 row(s) had M1 path evidence that the internal limit would have reached TP if filled.
- XAUUSD 2026-04-17 13:30 resolves as an internal intent lifecycle gap: log has placed=True, trigger=False, fill=False, discard=True; M1 counterfactual outcome=TP at 2026-04-17T15:40:00+00:00.
- Conclusion: broker-history backfill is not enough for this row; the unresolved part is why the live pending-fill branch did not log a trigger despite counterfactual M1 touch evidence.

## Rows

| Symbol | Candle close UTC | class | placed | triggered | filled | discarded | M1 outcome | M1 outcome time |
|---|---|---|---:|---:|---:|---:|---|---|
| XAUUSD | 2026-04-17T13:30:00+00:00 | discarded_internal_intent_but_research_path_would_have_filled | True | False | False | True | TP | 2026-04-17T15:40:00+00:00 |

## Ambiguity Ledger

- LIMIT_PLACED is an internal pending intent, not proof of a broker-resting pending order.
- Local logs do not record the M15 candle low/high fed into each pending-fill check, so a no-trigger row cannot be fully replayed from logs alone.
- M1 OHLC path simulation is counterfactual when no broker fill occurred; it cannot be counted as realized R.
- The XAUUSD 2026-04-17 13:30 row remains an execution-telemetry anomaly, not an orderflow-alpha datapoint.

## Open Questions

1. Why did the live pending-fill branch not log a trigger for XAUUSD 2026-04-17 13:30 when research M1 data later shows price traded through the internal limit?
2. Were M15 candles empty/stale in the live raw_data object during the pending-intent window?
3. Should pending-intent monitoring log the checked candle low/high on every active candle for future forensic closure?
4. Should outcome joins classify internal-intent counterfactual TP separately from broker-realized TP by default?

## Next Steps

1. Do not backfill XAUUSD 2026-04-17 13:30 as actual realized R unless broker deal evidence appears.
2. Keep the row out of promotion-grade orderflow scoring; use it only for execution telemetry forensics.
3. Add forward research telemetry for pending-intent checked candle high/low and trigger decision before relying on future limit-intent outcomes.
4. Keep synthetic/path labels and actual broker-R labels as separate fields in every orderflow report.
