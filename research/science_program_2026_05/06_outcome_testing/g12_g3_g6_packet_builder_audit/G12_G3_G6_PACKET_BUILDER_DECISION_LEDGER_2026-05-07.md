# G12 G3/G6 Packet Builder Audit Decision Ledger - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

No outcomes, broker actual-R, blocked packet outcomes, R/result statistics, paid/API/MT5/network calls, or live trading surfaces were opened.

## Decisions

| Packet | Experiment | Decision | Rows | Unique groups | Reason |
| --- | --- | --- | --- | --- | --- |
| OTG0-PKT-031 | EXP-G3-DC-OVERSHOOT-002 | ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY | 95 | 95 | Prior G12 zero-record blocker is cleared with source-hashed input-only rows, no forbidden result fields, separated labels, duplicate policy, and terminal-order unclaimed. Record count 95 remains below or unproven against sample floor: Minimum 250 deduped post-break rows and at least 40 rows in each overshoot quintile after symbol/session clustering. |
| OTG0-PKT-032 | EXP-G3-DC-SWING-001 | ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY | 8 | 8 | Prior G12 zero-record blocker is cleared with source-hashed input-only rows, no forbidden result fields, separated labels, duplicate policy, and terminal-order unclaimed. Record count 8 remains below or unproven against sample floor: Minimum 400 deduped candidate rows overall, minimum 60 per primary symbol cohort, and effective-N >= 100 after duplicate active setup clustering. |
| OTG0-PKT-036 | EXP-G3-TDA-007 | ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY | 96 | 96 | Prior G12 zero-record blocker is cleared with source-hashed input-only rows, no forbidden result fields, separated labels, duplicate policy, and terminal-order unclaimed. Record count 96 remains below or unproven against sample floor: Minimum 500 deduped candidate rows, effective-N >= 120, and max 12 preregistered TDA features before modeling. |
| OTG0-PKT-060 | G6-EXP-001-OB-VS-GENERIC-RETRACE | BLOCKED_WITH_NEXT_EXACT_QUESTION | 80 | 20 | Structured OB bounds are core to OB-vs-generic; verifier-text parsing is not strong enough for this packet to clear outcome-audit readiness. |
| OTG0-PKT-061 | G6-EXP-002-CONTINUATION-NO-RETRACE | BLOCKED_WITH_NEXT_EXACT_QUESTION | 51 | 8 | Exact executable decision price and ordered path are core to continuation/no-retrace lifecycle odds. |
| OTG0-PKT-062 | G6-EXP-003-OPENING-DRIVE-CONTINUATION | ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY | 86 | 19 | Prior G12 zero-record blocker is cleared with source-hashed input-only rows, no forbidden result fields, separated labels, duplicate policy, and terminal-order unclaimed. Record count 86 remains below or unproven against sample floor: 200 session-window breakout rows after duplicate and killed-route exclusions. |
| OTG0-PKT-063 | G6-EXP-004-EXHAUSTION-CHANGEPOINT | BLOCKED_WITH_NEXT_EXACT_QUESTION | 86 | 21 | A true preregistered changepoint source is core to the exhaustion/changepoint hypothesis; current fields are only OHLC proxy scaffolding. |
| OTG0-PKT-066 | G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE | BLOCKED_WITH_NEXT_EXACT_QUESTION | 7 | 6 | Structured liquidity-sweep fields are core to the round-number/OB confluence hypothesis. |
