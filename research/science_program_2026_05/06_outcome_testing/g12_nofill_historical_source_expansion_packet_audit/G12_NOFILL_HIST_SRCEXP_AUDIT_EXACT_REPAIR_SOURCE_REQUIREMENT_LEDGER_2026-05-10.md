# Exact Repair Source Requirement Ledger

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "exact_repair_source_requirement_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_repair_source_requirement_count": 3,
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "remaining_requirements": [
    {
      "exact_repair_requirement": "Separate source-expansion packet repair/rebuild route must refresh this parser/verifier hash in the target source-hash manifest and packet parser_code_hash fields, then rerun the target verifier/tests before any validation route opens.",
      "exists_now": true,
      "hash_matches_manifest": false,
      "issue": "strict_hash_mismatch",
      "manifest_sha256": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "role": "parser_or_verifier:builder",
      "source_contract_id": "route_parser_verifier_code"
    },
    {
      "exact_repair_requirement": "Separate source-expansion packet repair/rebuild route must refresh this parser/verifier hash in the target source-hash manifest and packet parser_code_hash fields, then rerun the target verifier/tests before any validation route opens.",
      "exists_now": true,
      "hash_matches_manifest": false,
      "issue": "strict_hash_mismatch",
      "manifest_sha256": "209f51ac1400e2dcb3d9eb0528a2bbcec1c95dfa3749b867d379f8ab18455567",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "472dd4b2be228bac59017b4aabb5934dfe150819fdc8007bcd08a9fa38ab75e1",
      "role": "parser_or_verifier:focused_tests",
      "source_contract_id": "route_parser_verifier_code"
    },
    {
      "exact_repair_requirement": "Separate source-expansion packet repair/rebuild route must refresh this parser/verifier hash in the target source-hash manifest and packet parser_code_hash fields, then rerun the target verifier/tests before any validation route opens.",
      "exists_now": true,
      "hash_matches_manifest": false,
      "issue": "strict_hash_mismatch",
      "manifest_sha256": "4a750bdf1fdb4c016c01fac04d69bbd40ee991275ad42bdb2ea1430ec5d333da",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "ebeae4746221ff30a968a41ef8a938bb15d6f1a1f9fc346621ccae6dcfbf9ea5",
      "role": "parser_or_verifier:verifier",
      "source_contract_id": "route_parser_verifier_code"
    }
  ],
  "terminal_implication": "ACCEPT_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS",
  "validation_safe": false
}
```
