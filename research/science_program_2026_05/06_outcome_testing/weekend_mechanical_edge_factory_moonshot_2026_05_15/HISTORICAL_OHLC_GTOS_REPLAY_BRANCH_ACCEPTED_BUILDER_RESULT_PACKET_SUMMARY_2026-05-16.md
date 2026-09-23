# Historical OHLC GTOS Replay Branch Accepted Builder Result Packet

Generated UTC: `2026-05-16T12:12:08Z`

Accepted-builder result packet only. It consumes branch parameter execution scoring rows and converts every branch/family into concrete next-layer branch-local builder, repair, or provenance decisions. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, live-readiness, promotion, or live effect.

## System Recommendation

EXECUTE_ACCEPTED_BUILDER_BRANCHES_NOW_AND_REJECT_OR_REPAIR_THE_REST: execute all accepted source/M15/M1/positive/entry-adverse builder rows, preserve binding provenance, and keep rejected rows only in explicit repair/avoid ledgers.

## Counts

- `input_execution_branch_rows`: `386`
- `input_execution_family_rows`: `1930`
- `input_execution_source_rows`: `138`
- `input_execution_m15_rows`: `186`
- `input_execution_m1_rows`: `110`
- `input_execution_positive_rows`: `243`
- `input_execution_entry_adverse_rows`: `386`
- `input_execution_binding_rows`: `2`
- `branch_result_rows`: `386`
- `family_result_rows`: `1930`
- `accepted_builder_rows`: `277`
- `rejected_repair_rows`: `109`
- `source_result_rows`: `138`
- `m15_result_rows`: `186`
- `m1_result_rows`: `110`
- `positive_result_rows`: `243`
- `entry_adverse_result_rows`: `386`
- `binding_result_rows`: `2`
- `bucket_rows`: `73`
- `question_rows`: `5`
- `source_manifest_rows`: `9`

## Branch Result Split

- `NEXT_LAYER_ACCEPTED_BUILDER_EXECUTE`: `277`
- `NEXT_LAYER_BINDING_PROVENANCE_PRESERVED`: `2`
- `NEXT_LAYER_REJECTED_REPAIR_OR_AVOID`: `107`