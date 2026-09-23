# Sierra SCID M15 Source-Bound Bar Packet

Generated UTC: `2026-05-15T17:13:01Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source-bound bar construction only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `scid_input_files`: `33`
- `source_audit_rows`: `33`
- `m15_bar_rows`: `250133`
- `gap_rows`: `21991`
- `question_rows`: `120`
- `raw_records_read`: `438806420`
- `invalid_records_skipped`: `3244050`
- `timestamp_nonmonotonic_pairs`: `189`
- `mutable_size_files`: `24`

## Parser Status Counts

- `SCID_PARSER_OK`: `9`
- `SCID_PARSER_OK_BYTE_RANGE_FREEZE_REPAIRED_MUTABLE_SIZE`: `24`

## Mutable Status Counts

- `CURRENT_FILE_LONGER_MUTABLE_APPEND_OR_REWRITE`: `24`
- `UNCHANGED_SIZE_FROM_SOURCE_LEDGER`: `9`

## Next Same-Resource Work

- Run a Sierra M15 primitive factory over this bar ledger.
- Compare Sierra futures proxy primitives against existing tick/MT5 Route C primitives on same sessions and horizons.
- Split exchange-calendar gaps from source-capture gaps before any completeness claim.
