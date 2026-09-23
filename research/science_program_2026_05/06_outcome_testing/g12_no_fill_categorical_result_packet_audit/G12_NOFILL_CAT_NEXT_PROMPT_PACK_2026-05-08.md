# G12 NOFILL CAT Next Prompt Pack - 2026-05-08

Recommended next lane: `NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1`.

Objective: split the 246 blocked categorical no-fill rows by blocker family and open only source-correction or contract-revision lanes needed to make future categorical lifecycle labels possible. Do not compute R, win rate, expectancy, broker actual-R, account history, live order/deal/position labels, hidden labels, validation, promotion, or live effect.

Starting facts to preserve:
- G12 accepted `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1` only as categorical lifecycle evidence for 52 `nofill_terminal_before_entry` rows.
- 246 rows remain blocked before label.
- Blocker counts: duplicate conflict 42; LTF price-only 69; missing pending-intent closure field 54; missing source/opening-drive prereg fields 80; separate fill/path plus terminal-order ambiguity 1.
- Row `NOFILL-CLOSE-ROW-0127` has OTR061 terminal first touch `2026-05-06T07:15:00.634000Z` and SHA256 `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`, but remains blocked until opening-drive prereg fields are source-hashed.
- Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Route order:
1. OTI4 opening-drive source-correction/contract-revision for range_high, range_low, breakout_close_time, breakout_side, and as-of provenance.
2. OTI1 pending-intent closure source packet for entry_touched_at_utc and fill/cancel/expiry/horizon timestamps without broker/account labels.
3. OTI3 USDJPY M1 price-only quote/tick replay or conservative quote contract.
4. OTI5 duplicate-conflict source identity/geometry audit.
5. OTI2 separate fill/path categorical contract for the single entry-touched ambiguous row if still needed.

Forbidden: no R/performance, no blocked CNR061/T3 scoring, no broker/account/live/order/hidden labels, no paid/API/Databento, no MT5 order/account/history calls, no live trading surface edits, no validation/promotion/live-effect flags.
