# G12 OTX G6 Next Lane Prompt Pack - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Accepted Follow-Up Lanes

1. `/goal Run the OTG0-PKT-062 OTI4B source-complete continuation follow-up from C:\tmp\gtos_otb\G12OTX using the G12 OTX G6 post-audit decision ledger and OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER as controlling inputs; use only source-complete future/additional opening-drive rows, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, keep broker actual-R/live order/paid/API sources closed, enforce one duplicate_breakout_key_otx denominator, stop with a blocker if fewer than 200 unique breakout groups are source-complete.`
2. `/goal Run the OTG0-PKT-063 CUSUM/changepoint quarantined result lane from C:\tmp\gtos_otb\G12OTX using G12_OTX_G6_POST_AUDIT_DECISION_LEDGER and OTX_G6_REBUILT_PACKET_PROPOSALS as controlling inputs; freeze the 81 source-ready rows only, exclude the five listed insufficient-predecision-M1 rows, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, do not inspect broker actual-R/live order/paid/API sources, and stop if duplicate/source/as-of checks fail before scoring.`
3. `/goal Run the OTG0-PKT-066 XAU sweep/round-number quarantined result lane from C:\tmp\gtos_otb\G12OTX using G12_OTX_G6_POST_AUDIT_DECISION_LEDGER and OTX_G6_REBUILT_PACKET_PROPOSALS as controlling inputs; freeze the three current source-ready rows only unless more source-ready XAU rows are captured, exclude the four listed tick-coverage blockers, require sample floor 150 before any result summary beyond parser dry-run, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, and keep broker actual-R/live order/paid/API sources closed.`

## Blocked Data/Instrumentation Tasks

- `OTG0-PKT-060`: no future result lane is justified until `mechanical_ob_bounds_asof_v1` captures H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, touch sequence, market_state source path/hash, and row hash for every row.
- `OTG0-PKT-061`: no future result lane is justified until XAUUSD ticks covering `2026-05-06T07:10:00Z` through at least `2026-05-06T11:15:00Z` are recovered or prospectively recaptured and hashed.

## Stop Conditions

- Stop immediately if a lane requires broker actual-R, account history, MT5 calls, live order state, paid/API/Databento calls, prompt/risk/execution/permission/safety/selector/canary edits, credentials, or remote pushes.
- Stop with an exact blocker if required source hashes, feature-as-of checks, duplicate denominator checks, JSON parsing, or focused tests fail.
- Do not use these prompts for promotion. They authorize quarantined discovery/control work only.
