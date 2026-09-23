# Sierra Parser Timestamp Repair

Generated UTC: `2026-05-15T16:49:53Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: Sierra parser/timestamp/source-byte repair only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `input_sierra_rows`: `262`
- `audit_rows`: `262`
- `byte_range_freeze_rows`: `262`
- `timestamp_contract_reuse_rows`: `4`
- `blocker_rows`: `269`
- `scid_rows`: `33`
- `depth_rows`: `227`
- `dly_rows`: `2`
- `parser_error_rows`: `0`
- `missing_file_rows`: `0`
- `mutable_size_rows`: `40`

## Parser Status Counts

- `DEPTH_PARSER_OK_BYTE_RANGE_FREEZE_REPAIRED_MUTABLE_SIZE`: `16`
- `DEPTH_PARSER_OK_SEGMENT_SAMPLE_AUDITED`: `211`
- `DLY_PARSER_NOT_IMPLEMENTED_METADATA_AND_SEGMENT_HASH_ONLY`: `2`
- `SCID_PARSER_OK`: `9`
- `SCID_PARSER_OK_BYTE_RANGE_FREEZE_REPAIRED_MUTABLE_SIZE`: `24`

## Mutable Size Status Counts

- `CURRENT_FILE_LONGER_MUTABLE_APPEND_OR_REWRITE`: `40`
- `UNCHANGED_SIZE_FROM_SOURCE_LEDGER`: `222`

## Remaining Same-Resource Work

- Run event-window depth replay for any specific feature claim instead of relying on sampled command counts.
- Build or route around the `.dly` parser gap before using Sierra daily files.
- Bind future Sierra-derived feature packets to the ledger-prefix byte range and segment hash family when files are mutable.
