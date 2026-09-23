# G12 NOFILL May 3 Decision Ledger - 2026-05-09

Generated: `2026-05-09T03:38:51Z`

Terminal decision: `ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY`

Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Row Decisions

| row | symbol | window_rows | first_tick | decision |
| --- | --- | --- | --- | --- |
| NOFILL-CAT-ROW-0049 | NAS100 | 0 | 2026-05-03T22:00:00.391000Z | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY |
| NOFILL-CAT-ROW-0050 | XAUUSD | 0 | 2026-05-03T22:00:00.780000Z | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY |
| NOFILL-CAT-ROW-0051 | XAUUSD | 0 | 2026-05-03T22:00:00.780000Z | ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY |

## Decision Rationale

The three rows exactly match the residual OTI4 May 3 blockers. The same-symbol broker tick files have zero ticks in the frozen `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z` range. First broker ticks arrive at `2026-05-03T22:00:00.391Z` for NAS100 and `2026-05-03T22:00:00.780Z` for XAUUSD. Independent official CME source checks support Sunday evening Globex open at `2026-05-03T22:00:00Z` for the NQ/GC proxy sessions.

Acceptance is narrow: source-control market-session-empty evidence only. It is not a result label, denominator admission, validation-safe flip, promotion, or live behavior change.

## Audit Question Answers

- Q1: Yes. The three target rows exactly match the residual OTI4 May 3 rows by row ID, symbol, source lane, source packet, source row, duplicate group, duplicate key, and original blocker code.
- Q2: Yes. G12 independently supports MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL for the three rows as source/control evidence only.
- Q3: Yes. NAS100 and XAUUSD broker tick parquets have zero rows in 2026-05-03T13:00:00Z through 13:30:00Z and first ticks at 22:00:00.391Z / 22:00:00.780Z.
- Q4: Yes. Official CME NQ and GC source checks support Sunday evening Globex open at 18:00 ET / 17:00 CT, which converts to 2026-05-03T22:00:00Z.
- Q5: Yes. UTC 13:00-13:30 converts to 08:00-08:30 America/Chicago and 09:00-09:30 America/New_York on 2026-05-03.
- Q6: Yes, narrowly. NAS100-to-NQ and XAUUSD-to-GC are acceptable only as market-session source-control proxies when paired with same-symbol broker quote zero-row evidence.
- Q7: Yes. Failed direct curl attempts are recorded as failed and used_for_factual_claims=false.
- Q8: Yes. All 36 upstream strict source hash records recompute against their recorded source paths.
- Q9: Yes. Sierra SCID files are supporting proxy/same-market zero-row checks and depth files are presence/hash only, not OHLC or quote proof.
- Q10: Yes. The 65 rejects, six T3 rows, G12-blocked CNR061 rows, and all other no-fill rows remain outside May 3 labels, denominators, result use, validation use, and promotion use.
- Q11: No generated or upstream-scanned artifact sets validation_safe=true, outcome_review_opened=true, or live_effect=true.
- Q12: No result/R/performance scoring, broker actual-R, account/order/history label, hidden label, or blocked-packet outcome use was found in this lane.
- Q13: G12 decision: ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY.
- Q14: No exact next source prompt remains for these three source-control rows. A future optional hardening route could export broker-native symbol-session metadata, but result lanes still remain closed unless separately frozen, approved, and no-leak verified.
