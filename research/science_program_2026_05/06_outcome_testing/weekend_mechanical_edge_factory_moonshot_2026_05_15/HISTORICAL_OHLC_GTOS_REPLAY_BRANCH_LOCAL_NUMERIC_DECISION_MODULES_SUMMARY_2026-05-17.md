# Branch-Local Numeric Decision Modules

Generated UTC: `2026-05-17T10:25:13Z`

Branch-local numeric decision modules. This packet consumes the numeric result ledger into executable research-only module records, scorer modules, avoid/inverse filters, source-geometry repair specs, context/stress modules, and per-row executable self-tests. It writes runnable module references and does not change live behavior, place orders, or claim live readiness.

## Counts

- `input_numeric_result_rows`: `17916`
- `input_source_geometry_repair_rows`: `17753`
- `numeric_decision_module_rows`: `17916`
- `scorer_module_rows`: `5341`
- `avoid_inverse_filter_rows`: `4115`
- `source_geometry_repair_spec_rows`: `17753`
- `context_stress_module_rows`: `1513`
- `self_test_rows`: `17916`
- `self_test_pass_rows`: `17916`
- `symbol_session_horizon_rollup_rows`: `347`
- `bucket_rows`: `45`
- `question_rows`: `4`
- `source_manifest_rows`: `8`

## Module Role Counts

- `AVOID_INVERSE_OR_FAILURE_FILTER_MODULE`: `4115`
- `CONTEXT_STRESS_OR_REDESIGN_MODULE`: `1513`
- `DEFAULT_OFF_NUMERIC_SCORER_MODULE`: `385`
- `DEFAULT_OFF_PROXY_CHALLENGER_SCORER_MODULE`: `4956`
- `SOURCE_GEOMETRY_REPAIR_MODULE`: `6947`

## Immediate Consumption

The module ledgers are executable against `src.research_infra.moonshot_numeric_decision_modules.execute_numeric_module_event`; the self-test ledger records one matching and one mismatching probe for every numeric row.
