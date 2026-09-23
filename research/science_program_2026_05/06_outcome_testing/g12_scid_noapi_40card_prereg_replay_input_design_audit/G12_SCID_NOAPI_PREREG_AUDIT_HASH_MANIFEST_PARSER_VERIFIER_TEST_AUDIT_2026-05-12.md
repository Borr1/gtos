# Hash Manifest Parser Verifier Test Audit

```json
{
  "artifact_family": "hash_manifest_parser_verifier_test_audit",
  "blocking_hash_mismatches": [],
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T13:39:30Z",
  "hash_binding_policy": "All target manifest artifacts except the manifest's self-entry must match. The self-entry is treated as a documented nonblocking follow-up because self-referential hashes cannot stabilize under the current target verifier.",
  "live_effect": false,
  "missing_manifest_artifacts": [],
  "nonblocking_manifest_self_hash_mismatches": [
    {
      "classification": "NONBLOCKING_SELF_REFERENTIAL_MANIFEST_HASH",
      "current_sha256": "8f43555a3dadf8a3a98c1e0ff34a390843cadb1d311d54d42ca8775dc4d8a0cd",
      "explanation": "The target manifest includes a hash of itself, which changes when the manifest is written. The G12 audit binds the current manifest hash independently instead of treating this self-entry as blocking.",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_OUTPUT_MANIFEST_2026-05-12.json",
      "recorded_sha256": "e0ff93ddd6f7c06b435d669fe97a06d5881a699cfacdf7743a764c82d32988f4"
    }
  ],
  "ok": true,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT",
  "schema_version": "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1",
  "target_evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "target_focused_tests_rerun": {
    "command": [
      "python",
      "-m",
      "pytest",
      "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
      "-q",
      "--basetemp",
      ".pytest_tmp/g12_target_route_from_audit"
    ],
    "ok": true,
    "returncode": 0,
    "stderr": [],
    "stdout": [
      ".....                                                                    [100%]",
      "============================== warnings summary ===============================",
      "..\\..\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475",
      "  C:\\Users\\MSI\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_cache\\v\\cache\\nodeids: [WinError 5] Access is denied: 'C:\\\\Users\\\\MSI\\\\Documents\\\\ai-trading-agent\\\\.pytest_cache\\\\v\\\\cache'",
      "    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))",
      "",
      "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html",
      "5 passed, 1 warning in 0.16s"
    ]
  },
  "target_manifest_artifact_count": 38,
  "target_manifest_rows": [
    {
      "current_sha256": "ba14f94358a44359f40adca05be409e5ea9074ac8ab692304e7cc4f064f30f09",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/.gitignore",
      "recorded_sha256": "ba14f94358a44359f40adca05be409e5ea9074ac8ab692304e7cc4f064f30f09"
    },
    {
      "current_sha256": "807550cd83c0a2023769458f180896c0c2ebc2d7b6f439b3c57819a066550642",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_LEDGER_2026-05-12.json",
      "recorded_sha256": "807550cd83c0a2023769458f180896c0c2ebc2d7b6f439b3c57819a066550642"
    },
    {
      "current_sha256": "e3aa4d51527844e55394a3822d223200c504f17ff008ea6c34794b114385d004",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_LEDGER_2026-05-12.md",
      "recorded_sha256": "e3aa4d51527844e55394a3822d223200c504f17ff008ea6c34794b114385d004"
    },
    {
      "current_sha256": "e1ace6d011fb4904a040debb04a8e93bb9abf4151e0aa9c48d02e83d08505d58",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_ROWS_2026-05-12.jsonl",
      "recorded_sha256": "e1ace6d011fb4904a040debb04a8e93bb9abf4151e0aa9c48d02e83d08505d58"
    },
    {
      "current_sha256": "d1f3c9edc3dd39e1506825d421d8b87c3af99bc60bf24b8a203d7305780e7f9b",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_COMPLETION_AUDIT_2026-05-12.json",
      "recorded_sha256": "d1f3c9edc3dd39e1506825d421d8b87c3af99bc60bf24b8a203d7305780e7f9b"
    },
    {
      "current_sha256": "5b3f2a427aef37b4fe4b2bfbb32f597732d7f28ad1d105f8745b7e976137568f",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_COMPLETION_AUDIT_2026-05-12.md",
      "recorded_sha256": "5b3f2a427aef37b4fe4b2bfbb32f597732d7f28ad1d105f8745b7e976137568f"
    },
    {
      "current_sha256": "cbb901fb2a61916f7e43bf3deb71c56165f0505875db1900d3c43fb2ab43b098",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_CONTEXT_ANCHOR_2026-05-12.json",
      "recorded_sha256": "cbb901fb2a61916f7e43bf3deb71c56165f0505875db1900d3c43fb2ab43b098"
    },
    {
      "current_sha256": "1918e681d88966336628046d92127e6fc98be4d73cd25b424257ac95438c535a",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_CONTEXT_ANCHOR_2026-05-12.md",
      "recorded_sha256": "1918e681d88966336628046d92127e6fc98be4d73cd25b424257ac95438c535a"
    },
    {
      "current_sha256": "64e2f5ea265036ad3cac4b20799023fbe50c3fa9b2d92b02e127cbdd9a743970",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
      "recorded_sha256": "64e2f5ea265036ad3cac4b20799023fbe50c3fa9b2d92b02e127cbdd9a743970"
    },
    {
      "current_sha256": "f0d4bea6aa4f90221ab1d985947723667240c844ca9daafd5b9f0e03c5b6ecf2",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_LEDGER_2026-05-12.md",
      "recorded_sha256": "f0d4bea6aa4f90221ab1d985947723667240c844ca9daafd5b9f0e03c5b6ecf2"
    },
    {
      "current_sha256": "2f7449d6f77a375490939dabc96b2b0bade44bd99cd9ca0ddc9a8a15af7f6d64",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_ROWS_2026-05-12.jsonl",
      "recorded_sha256": "2f7449d6f77a375490939dabc96b2b0bade44bd99cd9ca0ddc9a8a15af7f6d64"
    },
    {
      "current_sha256": "636407b05f1ed8b175612be7c6358c116fcf3fa3c8d1b97cabb2bdeaf32ff1e4",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_FOCUSED_TEST_RESULT_2026-05-12.json",
      "recorded_sha256": "636407b05f1ed8b175612be7c6358c116fcf3fa3c8d1b97cabb2bdeaf32ff1e4"
    },
    {
      "current_sha256": "e0cdbded19db27a911eb31b058b40e6aa339ef6f0d581ee9c103f82e2e6a22da",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_FOCUSED_TEST_RESULT_2026-05-12.md",
      "recorded_sha256": "e0cdbded19db27a911eb31b058b40e6aa339ef6f0d581ee9c103f82e2e6a22da"
    },
    {
      "current_sha256": "9fd6fc7b4aa10117d5b806b42a1b53fe8e1bac69c993e8abe24968a68241439f",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER_2026-05-12.json",
      "recorded_sha256": "9fd6fc7b4aa10117d5b806b42a1b53fe8e1bac69c993e8abe24968a68241439f"
    },
    {
      "current_sha256": "fb8bf376b9348463247938fbc38992c688c333daf191ac3e512e42da2fcd15ec",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER_2026-05-12.md",
      "recorded_sha256": "fb8bf376b9348463247938fbc38992c688c333daf191ac3e512e42da2fcd15ec"
    },
    {
      "current_sha256": "8f43555a3dadf8a3a98c1e0ff34a390843cadb1d311d54d42ca8775dc4d8a0cd",
      "is_manifest_self": true,
      "matches": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_OUTPUT_MANIFEST_2026-05-12.json",
      "recorded_sha256": "e0ff93ddd6f7c06b435d669fe97a06d5881a699cfacdf7743a764c82d32988f4"
    },
    {
      "current_sha256": "2e20b6f00683d056b962a8f4cbcb76049da19228bd259e224dfca48af40f93e0",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_OUTPUT_MANIFEST_2026-05-12.md",
      "recorded_sha256": "2e20b6f00683d056b962a8f4cbcb76049da19228bd259e224dfca48af40f93e0"
    },
    {
      "current_sha256": "d25d109139c0b002add1e168a4680b054ab4bdd68f0adb2a805b62eb33190fd8",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PARTITION_AND_FORWARD_CAPTURE_DEPENDENCY_LEDGER_2026-05-12.json",
      "recorded_sha256": "d25d109139c0b002add1e168a4680b054ab4bdd68f0adb2a805b62eb33190fd8"
    },
    {
      "current_sha256": "a2735908c8f8897099c243b5712773881ac7274dd3866f401b0bd0794f0b42a6",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PARTITION_AND_FORWARD_CAPTURE_DEPENDENCY_LEDGER_2026-05-12.md",
      "recorded_sha256": "a2735908c8f8897099c243b5712773881ac7274dd3866f401b0bd0794f0b42a6"
    },
    {
      "current_sha256": "8919cb7a1d747d98fc0bd17c238f0fb5b9bca65f0b00015c574276254c2b53b0",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.json",
      "recorded_sha256": "8919cb7a1d747d98fc0bd17c238f0fb5b9bca65f0b00015c574276254c2b53b0"
    },
    {
      "current_sha256": "03c530fffacbeca5e2705502eb2d2209891dfb489ff1594af91a44421ae12753",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.md",
      "recorded_sha256": "03c530fffacbeca5e2705502eb2d2209891dfb489ff1594af91a44421ae12753"
    },
    {
      "current_sha256": "feb7833c22cbbc5faa69d6d1243cc30275a5b3d2a2fb2ff02fd5c6a06573bbe2",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_REPLAY_INPUT_PACKET_DESIGN_LEDGER_2026-05-12.json",
      "recorded_sha256": "feb7833c22cbbc5faa69d6d1243cc30275a5b3d2a2fb2ff02fd5c6a06573bbe2"
    },
    {
      "current_sha256": "c1a73821a57c0e1b9c4bb4651dd4070b5530ecd5903c5cfdb926000abaaafb07",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_REPLAY_INPUT_PACKET_DESIGN_LEDGER_2026-05-12.md",
      "recorded_sha256": "c1a73821a57c0e1b9c4bb4651dd4070b5530ecd5903c5cfdb926000abaaafb07"
    },
    {
      "current_sha256": "b95a279c357740696e91dcc0aa16567064c61aac80936007e8d505662ab1a795",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_REPLAY_INPUT_PACKET_DESIGN_ROWS_2026-05-12.jsonl",
      "recorded_sha256": "b95a279c357740696e91dcc0aa16567064c61aac80936007e8d505662ab1a795"
    },
    {
      "current_sha256": "87f18616904e18495d70ed61af75da719b34ecb0d8163bf75e213c687c508c52",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER_2026-05-12.json",
      "recorded_sha256": "87f18616904e18495d70ed61af75da719b34ecb0d8163bf75e213c687c508c52"
    },
    {
      "current_sha256": "ea54278705f1e86e4da70157f58683c1d024ee7c3d82313503512736f1a006c7",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER_2026-05-12.md",
      "recorded_sha256": "ea54278705f1e86e4da70157f58683c1d024ee7c3d82313503512736f1a006c7"
    },
    {
      "current_sha256": "14c438aa7888bef60bf9571609a87531de0c76ebb01be6c607c393a9960f5dd1",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SATURATION_LEDGER_2026-05-12.json",
      "recorded_sha256": "14c438aa7888bef60bf9571609a87531de0c76ebb01be6c607c393a9960f5dd1"
    },
    {
      "current_sha256": "91e25284598b3fff355f24f335624e6501b884c3e6f560b7681a6992bd45851a",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SATURATION_LEDGER_2026-05-12.md",
      "recorded_sha256": "91e25284598b3fff355f24f335624e6501b884c3e6f560b7681a6992bd45851a"
    },
    {
      "current_sha256": "5e17cc49bde06d2225b395eb7ded1d423d660b4db9dc049306410f1e1ce10190",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER_2026-05-12.json",
      "recorded_sha256": "5e17cc49bde06d2225b395eb7ded1d423d660b4db9dc049306410f1e1ce10190"
    },
    {
      "current_sha256": "2a7c1efb161936f6c4d9c96d9319da7db5dea9cd630250cf4d8b144d4af1a3d3",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER_2026-05-12.md",
      "recorded_sha256": "2a7c1efb161936f6c4d9c96d9319da7db5dea9cd630250cf4d8b144d4af1a3d3"
    },
    {
      "current_sha256": "bf1216dbd969d3239c187a1f5d335e00a4fadbd967b46760e50ea38a57288e33",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.json",
      "recorded_sha256": "bf1216dbd969d3239c187a1f5d335e00a4fadbd967b46760e50ea38a57288e33"
    },
    {
      "current_sha256": "96ae9e43b725a871b0c8551b283aedf5d99fcecba6104b84d917bde3e4f1501d",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.md",
      "recorded_sha256": "96ae9e43b725a871b0c8551b283aedf5d99fcecba6104b84d917bde3e4f1501d"
    },
    {
      "current_sha256": "0e1d1d17bc45ce042163cf46ebd9eaef9a79bcdd51ef4437b58ffbb4882623f6",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_ROWS_2026-05-12.jsonl",
      "recorded_sha256": "0e1d1d17bc45ce042163cf46ebd9eaef9a79bcdd51ef4437b58ffbb4882623f6"
    },
    {
      "current_sha256": "a2581904157c893350459f43b79354b79ddf25158eb91db9e17572272644b0e1",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_VERIFICATION_RESULT_2026-05-12.json",
      "recorded_sha256": "a2581904157c893350459f43b79354b79ddf25158eb91db9e17572272644b0e1"
    },
    {
      "current_sha256": "e2c1a8d5e2bbd0d332a1850ecf475a2cca7cc3a5a383e0b7ddd2075925a2c1bb",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_VERIFICATION_RESULT_2026-05-12.md",
      "recorded_sha256": "e2c1a8d5e2bbd0d332a1850ecf475a2cca7cc3a5a383e0b7ddd2075925a2c1bb"
    },
    {
      "current_sha256": "2d0d5d4176248d533ad519eefc1828a13d9bb1b1cb549381d4e0ac33d89ffcf7",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/build_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
      "recorded_sha256": "2d0d5d4176248d533ad519eefc1828a13d9bb1b1cb549381d4e0ac33d89ffcf7"
    },
    {
      "current_sha256": "a77e94668e237db26d3356dc025c0d4b0ceb363f20f7c3a983d2793876028f4c",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
      "recorded_sha256": "a77e94668e237db26d3356dc025c0d4b0ceb363f20f7c3a983d2793876028f4c"
    },
    {
      "current_sha256": "8494b6a846ab65c3205f343bee0b11a06ae78687f86c37c61c664cbd002bc004",
      "is_manifest_self": false,
      "matches": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
      "recorded_sha256": "8494b6a846ab65c3205f343bee0b11a06ae78687f86c37c61c664cbd002bc004"
    }
  ],
  "target_parser_ast_parse": {
    "failures": [],
    "method": "ast_parse_no_bytecode",
    "ok": true
  },
  "target_route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "target_verifier_and_tests_passed": true,
  "target_verifier_rerun": {
    "command": [
      "python",
      "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
      "--json",
      "--no-write"
    ],
    "ok": true,
    "returncode": 0,
    "stderr": [],
    "stdout": [
      "{",
      "  \"blocked_dependency_count\": 32,",
      "  \"can_mark_goal_complete\": true,",
      "  \"card_count\": 40,",
      "  \"domain_count\": 8,",
      "  \"domain_counts\": {",
      "    \"adversarial_baselines_placebo_explanations\": 5,",
      "    \"behavioral_game_theory_session_participant_constraints\": 5,",
      "    \"execution_science_spread_slippage_fillability\": 5,",
      "    \"geometry_topology_path_shape\": 5,",
      "    \"macro_session_calendar_cross_asset_context\": 5,",
      "    \"microstructure_orderflow_liquidity_trapped_flow\": 5,",
      "    \"ml_meta_labeling_model_disagreement_uncertainty_controls\": 5,",
      "    \"stochastic_tail_hazard_first_passage\": 5",
      "  },",
      "  \"evidence_class\": \"SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY\",",
      "  \"expansion_candidate_count\": 8,",
      "  \"failure_count\": 0,",
      "  \"failures\": [],",
      "  \"live_effect\": false,",
      "  \"ok\": true,",
      "  \"opens_ai_api\": false,",
      "  \"opens_broker_account_order_history_deal_position_evidence\": false,",
      "  \"opens_live_trading_behavior\": false,",
      "  \"opens_paid_or_vendor_access\": false,",
      "  \"opens_result_scoring\": false,",
      "  \"opens_validation\": false,",
      "  \"outcome_review_opened\": false,",
      "  \"outside_current_gtos_ob_framing_count\": 33,",
      "  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",",
      "  \"readiness_split\": {",
      "    \"BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS\": 15,",
      "    \"BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION\": 17,",
      "    \"PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY\": 8",
      "  },",
      "  \"replay_packet_count\": 8,",
      "  \"route_id\": \"SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN\",",
      "  \"syntax_parse\": {",
      "    \"failures\": [],",
      "    \"method\": \"ast_parse_no_bytecode\",",
      "    \"ok\": true",
      "  },",
      "  \"validation_safe\": false",
      "}"
    ]
  },
  "validation_safe": false
}
```
