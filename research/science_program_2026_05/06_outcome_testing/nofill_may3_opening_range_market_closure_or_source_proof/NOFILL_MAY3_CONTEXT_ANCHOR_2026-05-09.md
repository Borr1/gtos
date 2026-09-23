# NOFILL May 3 Opening-Range Context Anchor

- Generated UTC: 2026-05-09T02:50:02Z
- Lane: NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF
- Controlling prompt: `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF_GOAL_PROMPT_2026-05-09.md`
- Git HEAD at build: `2304d5e5d81326955d3268d0e50164ce61906451`
- Branch at build: `nofill-may3-opening-range-source-proof`
- Frozen opening range: `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`
- Target rows only: `NOFILL-CAT-ROW-0049`, `NOFILL-CAT-ROW-0050`, `NOFILL-CAT-ROW-0051`.
- Terminal source/control status: `MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL` for all three target rows.
- Active question stack:
  - Is the May 3 13:00-13:30 UTC range a valid trading window for CME NQ/GC proxies? Answer: no, it is Sunday 08:00-08:30 CT before 17:00 CT open.
  - Do same-symbol broker tick files contain quotes in that window? Answer: no, both NAS100 and XAUUSD broker parquets have zero rows and first ticks after 22:00 UTC.
  - Are any labels, result outcomes, promotion decisions, or denominator moves opened? Answer: no.
  - Are duplicate identities preserved? Answer: yes; XAUUSD rows 0050/0051 retain the same duplicate key and remain outside denominators.

## Boundaries

- Source/control only.
- No result scoring, broker actual-R, account/order/history labels, hidden labels, paid/API/Databento calls, or live trading behavior changes.
- `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, `promotion_verdict=NO_PROMOTION_VERDICT`.
