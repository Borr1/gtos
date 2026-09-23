# Branch Replay Execution Packet

Generated UTC: `2026-05-16T08:47:12Z`

## Boundary

Branch replay execution packet only. It converts every branch code/replay proposal into same-resource work units, source/ordering execution classes, positive challenger execution classes, and blocker/repair classes. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

## Counts

- input_branch_code_replay_rows: 386
- input_code_surface_resolution_rows: 1428
- input_positive_replay_spec_rows: 243
- input_source_ordering_queue_rows: 386
- input_surface_inventory_rows: 17
- branch_replay_execution_rows: 386
- replay_execution_work_unit_rows: 1428
- source_ordering_execution_rows: 386
- positive_replay_execution_rows: 243
- blocker_repair_rows: 386
- bucket_rows: 55
- question_rows: 3
- source_manifest_rows: 17

## branch_execution_class

- BINDING_ONLY_NO_SCALAR_EXECUTION: 2
- ENTRY_REDESIGN_REPLAY_EXECUTION_READY: 6
- M15_INTERVAL_EXECUTION_FIRST: 119
- M1_FILL_BAR_INTERVAL_EXECUTION_FIRST: 70
- POSITIVE_CHALLENGER_REPLAY_EXECUTION_READY: 50
- RECOVERED_PROXY_KEY_REPAIR_EXECUTION_FIRST: 1
- SOURCE_STRESS_INTERVAL_EXECUTION_FIRST: 138

## source_execution_class

- SOURCE_BINDING_ONLY_NO_SCALAR: 2
- SOURCE_EXACT_CLEAN_COMPUTABLE_NOW: 16
- SOURCE_EXACT_REPAIR_COMPUTABLE_NOW: 59
- SOURCE_EXACT_UNAVAILABLE_STRESS_OR_ACQUIRE: 138
- SOURCE_M1_SPREAD_PROXY_COMPUTABLE_NOW: 171

## ordering_execution_class

- ORDERING_ALREADY_COLLAPSED_OR_NOT_REQUIRED: 44
- ORDERING_BINDING_ONLY_NO_SCALAR: 2
- ORDERING_M15_INTERVAL_BOUND: 186
- ORDERING_M1_CHRONOLOGY_COMPUTABLE_NOW: 43
- ORDERING_M1_FILL_BAR_INTERVAL_BOUND: 110
- ORDERING_RECOVERED_PROXY_REQUIRES_KEY_REPAIR: 1

## work_unit_execution_status

- BINDING_ONLY_NO_REPLAY: 4
- REVIEW_AND_ROUTE: 242
- RUNNABLE_CURRENT_PROXY_OR_REPAIR: 627
- RUN_M15_INTERVAL_REPLAY_FIRST: 186
- RUN_M1_FILL_BAR_INTERVAL_REPLAY_FIRST: 110
- RUN_SOURCE_STRESS_OR_ACQUISITION_FIRST: 259

## blocker_repair_class

- NO_BLOCKER_CURRENT_PROXY_OR_CONTROL: 56
- ORDERING_M15_INTERVAL_BOUND: 119
- ORDERING_M1_FILL_BAR_INTERVAL_BOUND: 70
- RECOVERED_PROXY_M1_KEY_REPAIR_REQUIRED: 1
- SOURCE_EXACT_UNAVAILABLE_ACQUIRE_OR_STRESS: 138
- TARGETSTOP_NA_BINDING_ONLY: 2
