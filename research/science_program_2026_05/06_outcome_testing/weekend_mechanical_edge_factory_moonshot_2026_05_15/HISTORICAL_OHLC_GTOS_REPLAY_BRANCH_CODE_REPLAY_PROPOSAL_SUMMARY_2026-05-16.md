# Branch Code Replay Proposal Packet

Generated UTC: `2026-05-16T08:29:04Z`

## Boundary

Branch-local code/replay proposal packet only. It maps every branch-local implementation candidate and positive challenger to research-tooling code surfaces, replay prerequisites, source/order blockers, and exact next computations. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

## Counts

- input_branch_candidate_rows: 386
- input_code_surface_rows: 1428
- input_positive_candidate_rows: 243
- branch_code_replay_rows: 386
- code_surface_resolution_rows: 1428
- positive_challenger_replay_spec_rows: 243
- source_ordering_replay_queue_rows: 386
- surface_inventory_rows: 17
- bucket_rows: 34
- question_rows: 3
- source_manifest_rows: 11

## surface_mode

- REPLAY_OR_PACKET_BUILDER_SCRIPT: 827
- RESEARCH_HELPER_MODULE: 601

## surface_file_status

- BRANCH_LOCAL_NEW_FILE_REQUIRED: 1428

## branch_priority

- BINDING_OR_CONTROL_SCOPE: 2
- ENTRY_REDESIGN_REPLAY_FIRST: 52
- ORDERING_COLLAPSE_OR_INTERVAL_FIRST: 190
- POSITIVE_CHALLENGER_REPLAY_FIRST: 4
- SOURCE_ACQUISITION_OR_STRESS_FIRST: 138

## positive_replay_status

- NOT_POSITIVE_CHALLENGER_SCOPE: 143
- REPLAYABLE_WITH_EXACT_REPAIR: 15
- REPLAYABLE_WITH_EXACT_REPAIR_AND_M1_FILL_BAR_INTERVAL: 10
- REPLAYABLE_WITH_M1_SPREAD_ADJUSTED_PROXY: 131
- STRESS_INTERVAL_ONLY_NOT_SCALAR_REPLAY: 87
