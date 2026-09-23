# GTOS Capability Limitation Closure Source Hash Manifest

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "source_hash_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T06:33:15Z",
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
  "record_count": 42,
  "records": [
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "e7bc1ecf6518045d191e3f1fcdee968135d6129014973ae45629560514242b6b",
      "path": ".context\\LIVE_STATE.md",
      "raw_sha256": "e5623f79195b7bd249e79d1d95f43061221b6d30493cc673fac2c4a4916b5ab1",
      "role": "control_doc:LIVE_STATE.md",
      "size_bytes": 13292
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "1bc8223169e150ed2d64dcc74c6656c5db469a86eb53943ac199a633a407b670",
      "path": ".context\\02_session_handoffs\\SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "raw_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "role": "control_doc:SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "size_bytes": 25348
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "e9ab075e12f81af1ce8a672cec09cc8253ce039658cdbc961a650bcbb477c0f2",
      "path": ".context\\00_core\\quick_reference_card.md",
      "raw_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "role": "control_doc:quick_reference_card.md",
      "size_bytes": 11078
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "7148de708d527e58ee53220b8fb5f2d2f50fd42887944f0c5c39c5870ec0dbc8",
      "path": ".context\\00_core\\research_operating_doctrine.md",
      "raw_sha256": "bed0ae8b92a000a28e4e4a3f07563abbc4913b37bc9ec3ad5cc71d07263dda6d",
      "role": "control_doc:research_operating_doctrine.md",
      "size_bytes": 14363
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "565d1eb4b68bf27ae8cbc3be6b9a3a2e16024623b084b21a34bc319611440797",
      "path": ".context\\00_core\\research_current_state.md",
      "raw_sha256": "c26cb5ddd6d658ffb97332f62944af2739ab64322f4cd8c50ba1ef5f05b21412",
      "role": "control_doc:research_current_state.md",
      "size_bytes": 688351
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "0cef82ce7430985eee2b5d2416a5826c9200681b49c0a7ce0766cd5eb96d020b",
      "path": ".context\\00_core\\goal_session_research_discipline.md",
      "raw_sha256": "2598a90a8bb2b5a8dd04c117324d6775f8ec7697e4f0abaeb19513af2baebc6c",
      "role": "control_doc:goal_session_research_discipline.md",
      "size_bytes": 29372
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "e90fae2f494219562f0497fa55236f36c8cdd574a79ccea2f9432b954b5acc35",
      "path": ".context\\00_core\\local_heavy_data_inventory.md",
      "raw_sha256": "b9941a0891ac3afd1ac42f41f59de594e974e928f2ddf08bccf9c237554a26fc",
      "role": "control_doc:local_heavy_data_inventory.md",
      "size_bytes": 7418
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "405bb04229ce8bda24895f8f47e33c866fb42532f691dacd162acafe2444e572",
      "path": ".context\\00_READING_ORDER.md",
      "raw_sha256": "2ec3964df18b42c89059de7cac803d96d9c30e9d330439000695cd444e0fecfc",
      "role": "control_doc:00_READING_ORDER.md",
      "size_bytes": 10847
    },
    {
      "classification": "control_context",
      "exists": true,
      "lf_normalized_text_sha256": "e89971140f0d9db7cb5a90db8763a5bd4209f1e458ae6153c58774a0eb208888",
      "path": "research\\science_program_2026_05\\04_goal_prompts\\GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
      "raw_sha256": "0561bdc6bdc4f364f2f3d889e2bce43d67b39daf99c23c53f3ab0eaf8cf4c481",
      "role": "control_doc:GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
      "size_bytes": 11010
    },
    {
      "classification": "strict_source_hash",
      "exists": true,
      "lf_normalized_text_sha256": "2c9480b476e0f032a7c1fe9c49e81fcd1ed181f5a1cb323443367c14a8f5a93d",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\gtos_research_capability_limitation_closure_control_route\\build_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
      "raw_sha256": "2c9480b476e0f032a7c1fe9c49e81fcd1ed181f5a1cb323443367c14a8f5a93d",
      "role": "route_code:builder",
      "size_bytes": 57489
    },
    {
      "classification": "strict_source_hash",
      "exists": true,
      "lf_normalized_text_sha256": "a7312aff40ac2bace82a26328f55be0a404758f56d0962e62830d5a93229e26d",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\gtos_research_capability_limitation_closure_control_route\\verify_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
      "raw_sha256": "a7312aff40ac2bace82a26328f55be0a404758f56d0962e62830d5a93229e26d",
      "role": "route_code:verifier",
      "size_bytes": 13471
    },
    {
      "classification": "strict_source_hash",
      "exists": true,
      "lf_normalized_text_sha256": "25abcd391342e409cb12284764a9aab37b2ea7e24619ff0b7385a265aa163d05",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\gtos_research_capability_limitation_closure_control_route\\test_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
      "raw_sha256": "25abcd391342e409cb12284764a9aab37b2ea7e24619ff0b7385a265aa163d05",
      "role": "route_code:focused_tests",
      "size_bytes": 4141
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "1047d21432a623e76b954bda71d9abc34e55c8d47f4bc55b3a4c36abc9c68d1a",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_55_FIELD_BINDING_CHECKLIST_2026-05-10.json",
      "raw_sha256": "5a0ac760125069d49c0f0d05299879e83f5ea3c2a7666338148237437c84cfd8",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_55_FIELD_BINDING_CHECKLIST_2026-05-10.json",
      "size_bytes": 39311
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "1bcc3c74c40305101455cda93b50cfc04b0e419029933330ce2697f1f5be37bf",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json",
      "raw_sha256": "f37fe2979592124bc652148a292f2c3f2a8534eae8d7f38b8475e9579ac06623",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json",
      "size_bytes": 43416
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "27e063b001199b308e7af792007cada796dbdcd57be4283831020804e2563692",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json",
      "raw_sha256": "b782691c8bb9d0beb8202e6ef7a5777bc70d5535b1f17732fac2c592751bfc60",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json",
      "size_bytes": 45004
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "f91e5e77de810af81e98129b720b0f94a74eefc87952dffe45d95bc637a02802",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
      "raw_sha256": "de2642202ecaea7376ff6a44fa024d4e9b0216e3c280b3ab2901aeb24797cefb",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
      "size_bytes": 1408
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "e180c448a927bb37a73c80535d493c8ec853127a8d5218a2b24cdd62e09e2be9",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.json",
      "raw_sha256": "03725456746dc04573c586add498b9056e8b5aef034243d1ed3925b795b5f6b9",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.json",
      "size_bytes": 9989
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "c02a7574df25990599c523ae9ceebdda1742bb497cd319824c9b31611896740f",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CONTAMINATION_PURGE_LEDGER_2026-05-10.json",
      "raw_sha256": "e5b3788d6c0979c8a75673976da084bd6777ece2cb80ab065bef7b2ef55ac57d",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_CONTAMINATION_PURGE_LEDGER_2026-05-10.json",
      "size_bytes": 2018
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "6afce122134c7a485a6141ac5b74e01b60c7d88185f6c20e44abd4665e6140fa",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CONTEXT_ANCHOR_2026-05-10.json",
      "raw_sha256": "9b9d41e9c6e95c7e5a3294207b5062f9588364321be9684c711fa73195107225",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_CONTEXT_ANCHOR_2026-05-10.json",
      "size_bytes": 2913
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "0080a30cfaed211d842104ed0c2eb2886ff9508bd51140bce8ca2a5dbd430fcd",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_DECISION_LEDGER_2026-05-10.json",
      "raw_sha256": "f6a0a0824795b092235d8c1a57333b20eb7fab89c2f7010ccb6018326588a4d3",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_DECISION_LEDGER_2026-05-10.json",
      "size_bytes": 1418
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "120e5795cd8d80667b236e75fd5d690bd2cd6f15ef1966cb8499704f46646e99",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json",
      "raw_sha256": "b76b6cb9c15579cd26ddf0ed3a25ee264ff7c45e62cf1cba8d83ada840cb3a6e",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json",
      "size_bytes": 3700
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "908cb2cce1e74ef916adb7d7944b69aea8e49041b03f5edefe3b6b03c44e8112",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_FORBIDDEN_REDACTED_STATUS_AUDIT_2026-05-10.json",
      "raw_sha256": "dc831d612dc1bedc5a88b75255220af48a6826a0724a64a6b6af997cc74c0e06",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_builder_local_tick_shadow_packet:NOFILL_HIST_SOURCE_EXPANSION_FORBIDDEN_REDACTED_STATUS_AUDIT_2026-05-10.json",
      "size_bytes": 4909
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "ccee27f42aec7bac5ad9744d6d0c6898bc1e839937425b04d37a829bda1a10fe",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_55_FIELD_BINDING_AUDIT_2026-05-10.json",
      "raw_sha256": "6d271e40810d968c0d221d6486675f7a571c1e5f2eda6019d9b49a6a3c72efad",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_55_FIELD_BINDING_AUDIT_2026-05-10.json",
      "size_bytes": 1395
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "1bf240ef3444512f5be96dbf72c81d45927090f3268fc1bba807ea6ee480e854",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_BLOCKER_REJECT_EXACTNESS_AUDIT_2026-05-10.json",
      "raw_sha256": "a630f0d3a9950a7fca78b1adc8ebd8100cd7c7c4e88a3e819e79335a4ecf9390",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_BLOCKER_REJECT_EXACTNESS_AUDIT_2026-05-10.json",
      "size_bytes": 37965
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "da730c29ecbcbc3ef68f886280b2babe3e61a237250e89acfd741ce7d3b23118",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_COMPLETION_AUDIT_2026-05-10.json",
      "raw_sha256": "8ba29e9a4b517a992bb58daecc52ab100613e80676261dbc58d4be0e22fd52aa",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_COMPLETION_AUDIT_2026-05-10.json",
      "size_bytes": 10173
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "fdc41c2d11b99bba74ee04b8d81d9650ad9eac3b0a981a557379cc48d7185c5f",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_CONTAMINATION_PURGE_EMBARGO_AUDIT_2026-05-10.json",
      "raw_sha256": "f7ac11dfafea6637fb2e3d0c00ae18a11d964b362dbe767a2638e29f391b7bac",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_CONTAMINATION_PURGE_EMBARGO_AUDIT_2026-05-10.json",
      "size_bytes": 2134
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "dbf118b44b5077f31870e082aa2f644b378babd529b474d860ad98763701b722",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_CONTEXT_ANCHOR_2026-05-10.json",
      "raw_sha256": "c1a580a44387be9256f848ba47ef1cbf8602796f61305e43f32b1ecd7cf7f891",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_CONTEXT_ANCHOR_2026-05-10.json",
      "size_bytes": 2141
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "103291473f1fd99df6e84fbceb492a1b2da4c5ea95a7e694b655eb07297eb5c3",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json",
      "raw_sha256": "789242fbcdcdc60e61ce7191ce34646e3c2620510daf0e64f5230f3390e77e40",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json",
      "size_bytes": 4148
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "158af447801b41e6b4eb5a8c05b7cdf8e30aefc7ac8c97015645d277aa7c3e23",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_DUPLICATE_DENOMINATOR_AUDIT_2026-05-10.json",
      "raw_sha256": "b0234941e80b134ec8e18a078dd0965f644c5aa771781bc5768dde12704486cc",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_DUPLICATE_DENOMINATOR_AUDIT_2026-05-10.json",
      "size_bytes": 1675
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "6fb8749f5a7f72bfd2f322bd8fc8d5e9ffdc07e6f3026f87fc3fdbba6de18bf6",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json",
      "raw_sha256": "e42be73da654eb39d3e8e92a8533c37ebaf38fd72faf99bb3067b96211b5f91c",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json",
      "size_bytes": 3773
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "e7881f97357ae4dfebed4919787b796b08c019e1ed9bba58803c859d6c070e5b",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_FORBIDDEN_REDACTED_NOLEAK_AUDIT_2026-05-10.json",
      "raw_sha256": "406d6c689b3d26505dc6eee3f3b3cf5f0455acdfbd1d11e7b332a1df4e6375f5",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_FORBIDDEN_REDACTED_NOLEAK_AUDIT_2026-05-10.json",
      "size_bytes": 1343
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "e823ab3b16ec533e3b72c2ade2772896a7035bbf976133aa50d3f1fa253c3ef6",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_packet_audit\\G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE20_EXTRACTION_FAIL_CLOSED_AUDIT_2026-05-10.json",
      "raw_sha256": "641f9919c5cf33cac4a78246fb4d0381f17cd340eafb9d310d309f7c9edbf698",
      "role": "nofill_control_artifact:g12_nofill_historical_source_expansion_packet_audit:G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE20_EXTRACTION_FAIL_CLOSED_AUDIT_2026-05-10.json",
      "size_bytes": 1186
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "2dda4378dfd212c0719d5da7b57cb6d7c417c0bfb0e48367655bc5bff53a1a7f",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_COMPLETION_AUDIT_2026-05-10.json",
      "raw_sha256": "9ff434901046386f2fa819079276f9d7b1461b6071cae5c803ecc16629071e96",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_COMPLETION_AUDIT_2026-05-10.json",
      "size_bytes": 22107
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "27f9ac16f6f338114eed64a43d2ccb3b365108c8ec238524d5a90d2557f9df2c",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_CONTEXT_ANCHOR_2026-05-10.json",
      "raw_sha256": "bdd225a1448fda74cdd9b12343d101483482f35f3c2b3c588ed006654da91d42",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_CONTEXT_ANCHOR_2026-05-10.json",
      "size_bytes": 2581
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "98b090dd0832ce75633f1adcec9c07c2bb255d63b87ac9b00549fee661cfa322",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_DECISION_LEDGER_2026-05-10.json",
      "raw_sha256": "0e6ca5c6ffc274adc353ea11a6727e1d137a5e8410e266fe672c0968d7edc165",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_DECISION_LEDGER_2026-05-10.json",
      "size_bytes": 1205
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "4bdcc1fff60ea75aaff180c23fa99f074df9a4eab3bbb9cb51d18f9f00a9b380",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_EXACT_G12_BLOCKER_CLOSURE_LEDGER_2026-05-10.json",
      "raw_sha256": "c2d063cfba9260f36340090a06ff3435cc756b12d8450637c6d9d9bb6bbf0f54",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_EXACT_G12_BLOCKER_CLOSURE_LEDGER_2026-05-10.json",
      "size_bytes": 3622
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "8aafe2538fc493fbaadb117fb6d70c97e24c26f1eade30775949241a18e10123",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_NOLEAK_SAFE_FLAG_CHECK_2026-05-10.json",
      "raw_sha256": "af581f416f0208918496927e33d2a69dae5b4b095deed78034244cab22127084",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_NOLEAK_SAFE_FLAG_CHECK_2026-05-10.json",
      "size_bytes": 3168
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "7cb6fdff80a4a8e4d7aba5084ec924d22ac7307030620418ba859c5b1c98875e",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_OUTPUT_MANIFEST_2026-05-10.json",
      "raw_sha256": "1332cd7be60f61dd366cae839c8ab4ee6f1c4e4da7fd163c254297bd5e9a18e9",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_OUTPUT_MANIFEST_2026-05-10.json",
      "size_bytes": 7968
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "4931af12196c2a39c2e942a32efe02173773b914017d893a8ebf5ba0fce99cee",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_PACKET_SHA_LEDGER_2026-05-10.json",
      "raw_sha256": "fbef8549102b80e472be977120db1c23e3b8ac5dd8ba25b8c570fcca113a323c",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_PACKET_SHA_LEDGER_2026-05-10.json",
      "size_bytes": 1639
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "78f7a6879d716dbeca4ce2d94a7a8b73095322e6aaf48fd48e129ec4666dddfd",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_RECOMPUTED_SOURCE_HASH_MANIFEST_2026-05-10.json",
      "raw_sha256": "e4de6f1d95b9f6a114dedef4e97942b28356cc1a71ad71bbb1d910df0b956484",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_RECOMPUTED_SOURCE_HASH_MANIFEST_2026-05-10.json",
      "size_bytes": 16862
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "a23529decd89f8e6218b9a91e14023f70d14b31f9073b0bbbddb8a1d111f9adf",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_2026-05-10.json",
      "raw_sha256": "65921465488319eb3d9349fb9e4dafd502c34404f2be81e0f016d5af6d14fc9b",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_2026-05-10.json",
      "size_bytes": 4779
    },
    {
      "classification": "prior_control_artifact",
      "exists": true,
      "lf_normalized_text_sha256": "3aa87a331aaf6c96ebbdbb1f216236cc79f65e4d31649142bf749972418598af",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_TARGET_ARTIFACT_MUTATION_LEDGER_2026-05-10.json",
      "raw_sha256": "91242f4bc63249381e91e19daa19ecc1eee3b749599be96f94b29c30f6d1f35e",
      "role": "nofill_control_artifact:nofill_historical_source_expansion_packet_parser_hash_repair_rebuild:NOFILL_HIST_SRCEXP_HASH_REPAIR_TARGET_ARTIFACT_MUTATION_LEDGER_2026-05-10.json",
      "size_bytes": 6787
    }
  ],
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
