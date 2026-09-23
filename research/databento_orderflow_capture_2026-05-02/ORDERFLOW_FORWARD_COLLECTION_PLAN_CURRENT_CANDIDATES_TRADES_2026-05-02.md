# Orderflow Forward Collection Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Collection verdict: `COLLECT_FORWARD_DISCIPLINED_NOT_REPLAY`

## Synthesis

The program is no longer blocked by vendor availability for CME futures windows, but it is still blocked by label quality, forward sample size, unsupported-symbol proxy mapping, and one pending-limit telemetry gap. The correct next move is disciplined forward collection, not a registered replay or promotion.

## Current Data Reality

- Current candidate-feature rows loaded: 518
- Manifest rows loaded at build: 518
- Current supported candidate count: 58
- Manifest supported candidates within available data cap: 58
- Manifest candidate events by symbol: {'GBPUSD': 21, 'NAS100': 12, 'US30_cash': 1, 'XAGUSD': 14, 'XAUUSD': 10}
- Current unsupported candidate count: 57
- Current unsupported candidate symbols: {'GBPJPY': 23, 'USDJPY': 34}
- Rows after manifest available-end cap (None): 0
- Candidates after available-end cap: 0

## Existing Fetch Coverage

| Schema | executed | blocked | groups | status counts | estimated cost |
|---|---:|---:|---:|---|---:|
| trades | True | False | 13 | {'cached': 1, 'fetched': 12} | $0.635717 |
| mbp1 | True | False | 4 | {'fetched': 4} | $2.279908 |
| mbp10 | True | False | 4 | {'fetched': 4} | $4.672899 |

## Feature Diagnostics

| Schema | primary ok rows | candidate rows | context rows | synthetic winners | synthetic losers |
|---|---:|---:|---:|---:|---:|
| trades | 58 | 58 | 0 | 0 | 0 |
| mbp1 | 45 | 13 | 32 | 3 | 10 |
| mbp10 | 45 | 13 | 32 | 3 | 10 |

## Coverage By Symbol

| Symbol | rows | synthetic labels | actual R | synthetic outcomes | coverage classes |
|---|---:|---:|---:|---|---|
| GBPUSD | 21 | 9 | 0 | {'NO_ENTRY': 12, 'TP': 9} | {'limit_placed_no_broker_close_in_join': 2, 'no_actual_by_design_pre_execution_reject': 19} |
| NAS100 | 12 | 11 | 1 | {'SL': 10, 'TP': 1, 'none': 1} | {'actual_realized_r_available': 1, 'candidate_join_missing': 1, 'no_actual_by_design_pre_execution_reject': 10} |
| US30 | 1 | 0 | 0 | {'NO_ENTRY': 1} | {'no_actual_by_design_pre_execution_reject': 1} |
| XAGUSD | 14 | 0 | 0 | {'none': 14} | {'candidate_join_missing': 14} |
| XAUUSD | 10 | 2 | 0 | {'TP': 2, 'none': 8} | {'candidate_join_missing': 8, 'limit_placed_no_broker_close_in_join': 1, 'no_actual_by_design_pre_execution_reject': 1} |

## Collection Actions

| Priority | Action | Status | Scope | Policy |
|---:|---|---|---|---|
| 1 | A1_NAS100_FORWARD_LABEL_AND_DEPTH_COLLECTION | COLLECT_FORWARD_NOT_REPLAY | NAS100 GTOS CANDIDATE rows plus pre-declared matched context rows | Forward collect trades + MBP-1 for every new supported NAS100 candidate; collect MBP-10 only for pre-declared candidate/comparator windows. |
| 2 | A2_XAUUSD_LIMIT_INTENT_TELEMETRY | BLOCKED_BY_MISSING_LIVE_TELEMETRY | XAUUSD LIMIT_PLACED rows and future pending-limit lifecycle rows | Do not fetch more market data for the audited historical row; the missing evidence is live pending-intent candle telemetry. |
| 3 | A3_XAUUSD_CONTINUATION_CONTRAST | WAIT_FOR_LABEL_CONTRAST | XAUUSD CANDIDATE rows | Keep trades collection for new XAUUSD candidates; add MBP-1/MBP-10 only after both winner and loser labels exist. |
| 4 | A4_UNSUPPORTED_SYMBOL_PROXY_MAPPING | BLOCKED_BY_PROXY_MAPPING | Symbols in current candidate-feature log without validated CME proxy mapping | Do not pull futures data for unsupported symbols until a proxy mapping and timestamp policy are registered. |
| 5 | A5_MBO_QUEUE_BEHAVIOR | DEFERRED_NOT_REGISTERED | Order identity, queue churn, iceberg/refresh behavior | Keep MBO deferred until a registered MBP-10 question cannot be answered with top-10 depth. |

## Answered Questions

1. Current Databento trades data covers the existing supported manifest, but trades alone cannot reproduce heatmap/resting-liquidity behavior.
2. MBP-10 is more relevant than MBP-1 for ladder-depth questions, but the current MBP-10 candidate sample is below registration gate.
3. NAS100 loser labels are present; the harder blocker is the winner side plus actual broker-R coverage.
4. The XAUUSD LIMIT_PLACED anomaly is not recoverable as actual R from current local evidence.
5. MBO is not justified yet because no registered question has exhausted MBP-10.

## Ambiguity Ledger

- Forward candidate labels will arrive slowly and may remain imbalanced by symbol/session.
- Actual broker-R coverage is sparse because many orderflow candidate rows are pre-execution rejects by design.
- Unsupported symbols in the current shadow log need validated proxy mapping before futures orderflow can be used.
- The current timestamp policy is strong for tested 2026 windows but still lacks November fallback and contract-roll validation.
- MBP-10 one-second sampled snapshots do not prove order identity, iceberg behavior, or queue position.

## Open Questions

1. Does the NAS100 thin-depth failure signature persist in future, pre-declared candidate windows?
2. Can NAS100 collect enough winner labels without changing strategy parameters or mining thresholds?
3. Do actual broker fills eventually agree with synthetic/path labels, or do execution effects dominate?
4. Which unsupported GTOS symbols deserve validated futures-proxy mapping next, and are their proxies conceptually close enough?
5. Does any depth feature add value after symbol, session, label type, and timestamp policy are controlled?
6. What pending-intent telemetry is minimally sufficient to close future LIMIT_PLACED/no-fill ambiguities?

## Next Steps

1. Use A1 as the next collection rule: trades + MBP-1 for every new NAS100 candidate, MBP-10 only for pre-declared candidate/comparator windows.
2. Do not register the NAS100 replay hypothesis until actual-R, winner-count, and MBP-10 candidate gates are cleared or deliberately revised before looking at new data.
3. Keep XAUUSD continuation as a watchlist item until both winner and loser labels exist; do not spend broad depth credits on unlabeled rows.
4. Draft a research-only pending-intent telemetry spec before relying on future LIMIT_PLACED labels.
5. Validate proxy mapping for any new symbol before pulling paid futures orderflow for it.
6. Keep all future reports label-type separated: synthetic/path, actual broker R, and fill/no-fill.
