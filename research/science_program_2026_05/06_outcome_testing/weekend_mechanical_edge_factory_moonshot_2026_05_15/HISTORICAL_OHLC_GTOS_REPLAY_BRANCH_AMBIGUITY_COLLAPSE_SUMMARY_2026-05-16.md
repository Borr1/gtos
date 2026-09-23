# Historical OHLC GTOS Branch Ambiguity-Collapse Packet

Generated UTC: 2026-05-16T07:06:52Z

## Boundary

Historical OHLC GTOS branch ambiguity-collapse packet only. Rows preserve all 386 branches and classify same-M15 target/stop ambiguity, existing M1 replay or fill-bar stress evidence, interval preservation, target/stop NA binding, source confidence, duplicate/effective-N, concentration, and same-resource next actions. Exact broker R/PnL, strategy expectancy, win-rate, validation, live-readiness, promotion, and live behavior change are not claimed.

## Counts

- matrix_branch_input_rows: 386
- matrix_ambiguity_input_rows: 386
- matrix_source_repair_input_rows: 386
- source_repair_feasibility_input_rows: 386
- rstyle_branch_input_rows: 386
- m15_path_ambiguity_input_rows: 9185
- m1_replay_input_rows: 2256
- m1_fill_bar_stress_input_rows: 2256
- recovered_signature_path_input_rows: 816
- targetstop_na_branch_input_rows: 2
- targetstop_na_candidate_input_rows: 128
- targetstop_na_contract_input_rows: 32
- branch_classification_rows: 386
- m15_same_bar_classification_rows: 386
- m1_stress_join_rows: 386
- ordering_route_rows: 386
- interval_preservation_rows: 386
- targetstop_na_binding_rows: 162
- action_rows: 386
- bucket_rows: 45
- question_rows: 5
- source_manifest_rows: 12

## Ambiguity Collapse Distribution

- M15_SAME_BAR_NO_EXISTING_M1_INTERVAL_PRESERVED: 186
- M1_CHRONOLOGICAL_REPLAY_AVAILABLE_FOR_COLLAPSE: 43
- M1_FILL_BAR_STRESS_AVAILABLE_INTERVAL_BOUND_PRESERVED: 110
- NO_COLLAPSE_REQUIRED_ORDERED_PROXY_PRESERVED: 44
- RECOVERED_FILL_PATH_PRESENT_WITHOUT_M1_REPLAY_KEY: 1
- TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY: 2
