# G12 SCID FC Impl Design Audit Source Hash Manifest Binding

```json
{
  "artifact_count": 33,
  "artifact_type": "source_hash_manifest_binding_audit",
  "blocking_unrepaired_hash_mismatches": [],
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T08:02:20Z",
  "manifest_hash_mismatches": [
    {
      "actual_sha256": "5daaee001f8749cdfa772499b527bf37102c90479b28126758ef93c3d953e48f",
      "manifest_sha256": "599b18843a90799b9640f3f890b1a81ff4a8bb4a351ab34c8780c1576cb5106b",
      "path": "SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_2026-05-12.md",
      "repair_class": "CURRENT_G12_PROMPT_HARDENING_REBOUND_NONBLOCKING"
    },
    {
      "actual_sha256": "c773b4a672d37f8b3fe305672c3ac3fa2fbaedcde3616418b9b5a64d1d7e1c8e",
      "manifest_sha256": "14811ac73ae14554ed4535607cdca272ff1eec8687b5416f1e621a49da1f036f",
      "path": "SCID_FC_IMPL_DESIGN_G12_AUDIT_STARTER_2026-05-12.txt",
      "repair_class": "CURRENT_G12_PROMPT_HARDENING_REBOUND_NONBLOCKING"
    }
  ],
  "missing_manifest_artifacts": [],
  "parser_verifier_hashes": {
    "route_local_prompt": "5daaee001f8749cdfa772499b527bf37102c90479b28126758ef93c3d953e48f",
    "target_builder": "f0cf1ccfc7f3d30b5b4f0409c260351ffa4a8a0b08932dd792ea489b45fd3a9e",
    "target_tests": "af8fa6f4fed59638fa24dfb52c41cf221a22a4da20e347a53e779e84790b48a1",
    "target_verifier": "9ecc57da2dfccf7407b28eafe4c9f97718380bc54b3a8bc68c8f388b40df6315",
    "wrapper_prompt": "4dd20496fa66a4a950951fa08915b4e8defba99df9cb28f33da8fbb9df0487cf"
  },
  "prompt_hardening_repair": "The only accepted mismatch class is current G12 prompt/starter hardening after the implementation-design package was built. The audit rebinds current hashes here; all design payload, parser, verifier, test, patch, and upstream-source hashes remain strict.",
  "route_id": "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT",
  "safe_flags": {
    "live_effect": false,
    "opens_ai_api": false,
    "opens_broker_account_order_history_deal_position_evidence": false,
    "opens_live_behavior": false,
    "opens_live_restart": false,
    "opens_paid_vendor_access": false,
    "opens_prompt_config_risk_safety_execution_canary_selector_change": false,
    "opens_raw_market_data_blob_commit": false,
    "opens_registry_edit": false,
    "opens_remote_push": false,
    "opens_result_scoring": false,
    "opens_strategy_edge_review": false,
    "opens_validation": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": false
  },
  "target_manifest": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_2026-05-12.json",
  "target_manifest_hash": "e9e4729d15d2cd5ab69fb3d30cd948a11c1f6c5c63070b4e423d13f6a8cad4c1"
}
```
