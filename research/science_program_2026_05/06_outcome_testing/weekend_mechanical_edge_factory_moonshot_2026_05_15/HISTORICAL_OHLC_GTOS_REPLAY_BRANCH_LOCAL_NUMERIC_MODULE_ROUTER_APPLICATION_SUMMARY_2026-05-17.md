# Branch-Local Numeric Module Router Application

Generated UTC: `2026-05-17T10:44:20Z`

Branch-local numeric module router application. This packet runs executable numeric decision modules against all numeric result rows, emits scorer/avoid/source-repair/context outputs, executes source-repair specs into exact current-packet repair statuses, and writes scope decisions. It does not place orders or change live behavior.

## Counts

- `input_numeric_result_rows`: `17916`
- `input_numeric_decision_module_rows`: `17916`
- `input_source_repair_spec_rows`: `17753`
- `event_application_rows`: `17916`
- `scorer_output_rows`: `5341`
- `avoid_filter_output_rows`: `4115`
- `source_repair_output_rows`: `6947`
- `context_stress_output_rows`: `1513`
- `source_repair_execution_rows`: `17753`
- `source_repair_exact_current_packet_possible_rows`: `0`
- `scope_decision_rows`: `290`
- `bucket_rows`: `35`
- `question_rows`: `4`
- `source_manifest_rows`: `9`

## Router Actions

- `BIND_CONTEXT_STRESS_GUARD_SURFACE`: `1513`
- `EXECUTE_SOURCE_GEOMETRY_REPAIR_PATH`: `6947`
- `REGISTER_AVOID_INVERSE_FILTER_SURFACE`: `4115`
- `REGISTER_DEFAULT_OFF_SCORER_SURFACE`: `5341`
