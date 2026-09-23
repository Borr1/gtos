# G12 NOFILL CAT V3 Decision Ledger - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.

Overall decision: `ACCEPT_V3_AS_SOURCE_CONTROL_CATEGORICAL_INPUT_EVIDENCE_ONLY`.

Scope: source-control/categorical-input evidence only. No result scoring, validation-safe flip, promotion, or live effect is opened.

## Target Row Decisions

| packet_row_id | symbol | evidence_class | g12_terminal_decision | accepted_denominator | audit_passed |
| --- | --- | --- | --- | --- | --- |
| NOFILL-CAT-ROW-0049 | NAS100 | source_control | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0050 | XAUUSD | source_control | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0051 | XAUUSD | source_control | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0130 | USDJPY | source_impossible | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0143 | USDJPY | source_impossible | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0165 | USDJPY | source_impossible | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0178 | USDJPY | source_impossible | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | False | True |
| NOFILL-CAT-ROW-0241 | XAUUSD | source_control | ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE | False | True |

## Counterargument

Strongest counterargument: The strongest counterargument is that the V3 rebuild could be laundering previously blocked rows into accepted denominator rows or relying on stale source hashes.

Audit answer: The audit re-counts all 298 row IDs exactly once, verifies source-control and source-impossible rows have no labels and no accepted-denominator membership, replays source-control tick checks, rechecks USDJPY quote-state ambiguity from source parquet, recomputes 343 source-hash records with only mutable-context and line-ending exceptions, and keeps the next route as a separate evidence-class gate.
