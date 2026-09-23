# G12 NOFILL CAT Blocker Review

Status: `PASS`
Blocked rows: `246`
No blocked row relabelable under current contract: `true`

## Families
- `BLOCK_RESULT_DUPLICATE_CONFLICT`: `42` rows, `BLOCK_IS_CORRECT`.
  Next: Run a duplicate-source audit that proves whether each repeated row is one opportunity representation or a separate source identity, then freeze canonical geometry before labels.
- `BLOCK_RESULT_LTF_PRICE_ONLY`: `69` rows, `BLOCK_IS_CORRECT`.
  Next: Open a separate source-correction lane with source-hashed USDJPY tick/quote replay or an accepted conservative quote contract, then rerun categorical eligibility.
- `BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD`: `54` rows, `BLOCK_IS_CORRECT`.
  Next: Future logger/source packet must carry pending_created_at_utc, entry_touched_at_utc, fill/cancel/expiry/horizon timestamps and hashes without broker/account labels.
- `BLOCK_RESULT_MISSING_SOURCE`: `80` rows, `BLOCK_IS_CORRECT`.
  Next: Run a source-complete opening-drive correction/contract-revision lane that source-hashes range_high, range_low, breakout_close_time, breakout_side, and as-of provenance.
- `BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED`: `1` rows, `BLOCK_IS_CORRECT`.
  Next: Open a fill/path categorical contract if needed, preserving entry-touch and terminal-order ambiguity without R scoring.
- `BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS`: `1` rows, `BLOCK_IS_CORRECT`.
  Next: Use source-hashed tick/quote sequence proof in a separate fill/path contract.

## OTX Ambiguity
OTX/G12 post-audit accepted OTG0-PKT-062 only as quarantined discovery and future-lane evidence; it does not supply accepted source-complete opening-drive fields for this categorical no-fill packet.
