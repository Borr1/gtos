# G12 CNR061 Source Hash Join Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `audit_status`: `PASS_ACCEPTABLE_SOURCE_HASH_JOIN_WITH_MUTABLE_CONTEXT_STALENESS_NOT_ROW_BLOCKING`

```json
{
  "absolute_local_heavy_filename_searches": [
    {
      "errors": [],
      "exists": true,
      "matched_path_count_returned": 21,
      "matched_paths": [
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
      ],
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
      "search_limit_note": "filename-only search capped at 80",
      "visited_files_until_limit": 1158
    },
    {
      "errors": [],
      "exists": true,
      "matched_path_count_returned": 21,
      "matched_paths": [
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
      ],
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "search_limit_note": "filename-only search capped at 80",
      "visited_files_until_limit": 80
    },
    {
      "errors": [],
      "exists": true,
      "matched_path_count_returned": 80,
      "matched_paths": [
        "C:\\tmp\\LIVE_STATE_before_otr061_merge_20260507_173102.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\build_cnr061_geometry_horizon_sidecar_2026_05_08.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_GOAL_PROMPT_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_JOIN_MAP_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\test_cnr061_geometry_horizon_sidecar_2026_05_08.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\verify_cnr061_geometry_horizon_sidecar_2026_05_08.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\__pycache__\\build_cnr061_geometry_horizon_sidecar_2026_05_08.cpython-313.pyc",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\__pycache__\\test_cnr061_geometry_horizon_sidecar_2026_05_08.cpython-313-pytest-9.0.2.pyc",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\__pycache__\\test_cnr061_geometry_horizon_sidecar_2026_05_08.cpython-313.pyc",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\__pycache__\\verify_cnr061_geometry_horizon_sidecar_2026_05_08.cpython-313.pyc",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\build_g12_oti5_otr061_post_audit_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\test_g12_oti5_otr061_post_audit_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\OTI6_OTR061_CNR_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\build_otr061_xau_tick_recovery_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_COMPLETION_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_COMPLETION_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_GOAL_PROMPT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\test_otr061_xau_tick_recovery_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\build_g12_oti5_otr061_post_audit_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\test_g12_oti5_otr061_post_audit_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\OTI6_OTR061_CNR_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-07.md",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\build_otr061_xau_tick_recovery_2026_05_07.py",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_COMPLETION_AUDIT_2026-05-07.json",
        "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_COMPLETION_AUDIT_2026-05-07.md"
      ],
      "root": "C:\\tmp",
      "search_limit_note": "filename-only search capped at 80",
      "visited_files_until_limit": 20286
    },
    {
      "errors": [],
      "exists": true,
      "matched_path_count_returned": 2,
      "matched_paths": [
        "C:\\SierraChart\\Data\\XAUUSD.dly",
        "C:\\SierraChart\\Data\\XAUUSD.scid"
      ],
      "root": "C:\\SierraChart",
      "search_limit_note": "filename-only search capped at 80",
      "visited_files_until_limit": 337
    }
  ],
  "access_request_status": "NO_ACCESS_REQUEST_NEEDED_APPROVED_LOCAL_ROOTS_READABLE_FOR_SOURCE_SAFE_SCOPE",
  "artifact_family": "G12_CNR061_SOURCE_HASH_JOIN_AUDIT",
  "audit_status": "PASS_ACCEPTABLE_SOURCE_HASH_JOIN_WITH_MUTABLE_CONTEXT_STALENESS_NOT_ROW_BLOCKING",
  "control_artifact_current_hashes": [
    {
      "exists": true,
      "name": "cnr_matrix",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
      "sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5"
    },
    {
      "exists": true,
      "name": "cnr_next_route",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
      "sha256": "cc819f69aea3321a6fd26ec05dba6683c2d06454ea1dce7131812de2cc3516e1"
    },
    {
      "exists": true,
      "name": "cnr_noleak_duplicate",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
      "sha256": "798e5af02c55ddd85b8d67aeca7ecd7861657bdacb43708b532ceb238c596d55"
    },
    {
      "exists": true,
      "name": "cnr_source_rows",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
      "sha256": "883525dae5981227ffcddc0e819bb269585367c315b8568975d214212239c7bb"
    },
    {
      "exists": true,
      "name": "g12_blockers",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json",
      "sha256": "f56966f12e59ddd6ecd1a694beb9d6f642ac3d75342895ddc075d9b7c7eb5de4"
    },
    {
      "exists": true,
      "name": "g12_duplicate",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-08.json",
      "sha256": "afc7e1d09f30f72cd9a54ef3261b18c34ce83014a53a21db379ced0e87d4475a"
    },
    {
      "exists": true,
      "name": "g12_noleak",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_NOLEAK_AND_LABEL_AUDIT_2026-05-08.json",
      "sha256": "59b92da07372232f4efb52a1d4f83519058bdb202eb5b0361d232c9f722967a1"
    },
    {
      "exists": true,
      "name": "g12_oti7_blocker_map",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_2026-05-08.json",
      "sha256": "dbcc7db56b303a400dea8bc2d5146bcb0c4234f346850cfb4d273aec03f46129"
    },
    {
      "exists": true,
      "name": "g12_otr061_recovery",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
      "sha256": "3de2d8b35d272705df241a4bbc38ab2534273b5e4b6e4d6bdccc4353182e3b21"
    },
    {
      "exists": true,
      "name": "g12_ready",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json",
      "sha256": "ef9feef8508c069eac6328fcfd450476bb76862c25f3ec8a7433a1307114e499"
    },
    {
      "exists": true,
      "name": "g12_source_hash_asof",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json",
      "sha256": "b84516c6758254ac695fff59dded2c0352948498a1442c9ebc908dd0b4f3bd8e"
    },
    {
      "exists": true,
      "name": "g6_input_packet",
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a"
    },
    {
      "exists": true,
      "name": "goal_discipline",
      "path": ".context/00_core/goal_session_research_discipline.md",
      "sha256": "d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994"
    },
    {
      "exists": true,
      "name": "goal_prompt",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_SIDECAR_REAUDIT_GOAL_PROMPT_2026-05-08.md",
      "sha256": "c50c77d5b94ce7ac7909972b867e437f4b8f1b75e634d7f2e663c9ee5339825a"
    },
    {
      "exists": true,
      "name": "latest_handoff",
      "path": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235"
    },
    {
      "exists": true,
      "name": "live_state",
      "path": ".context/LIVE_STATE.md",
      "sha256": "39b1d1e896f3b6121cf9aafe88e98d00ec9317aac80781adf78e3fe614601d42"
    },
    {
      "exists": true,
      "name": "local_heavy_inventory",
      "path": ".context/00_core/local_heavy_data_inventory.md",
      "sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0"
    },
    {
      "exists": true,
      "name": "otr061_proposal",
      "path": "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
      "sha256": "d5a67175ab1da11941d29440e4b490b12648a3da60cd5c0bc45d4ebec7e7bc01"
    },
    {
      "exists": true,
      "name": "otx_proposals",
      "path": "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
      "sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224"
    },
    {
      "exists": true,
      "name": "quick_reference",
      "path": ".context/00_core/quick_reference_card.md",
      "sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd"
    },
    {
      "exists": true,
      "name": "research_current_state",
      "path": ".context/00_core/research_current_state.md",
      "sha256": "38a4084d8d2e41f869aa673dc47b25cc7667efa3aa10ec1190c9308eb32364ab"
    },
    {
      "exists": true,
      "name": "research_doctrine",
      "path": ".context/00_core/research_operating_doctrine.md",
      "sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe"
    },
    {
      "exists": true,
      "name": "sidecar_blockers",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
      "sha256": "e5c4e4985f4f26786a477cc95e607d082f037c743fda866d8337ca8a53ed3ce2"
    },
    {
      "exists": true,
      "name": "sidecar_completion",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
      "sha256": "36c171012876fd3e708c8791f0092787a4f15c5c43f43bfd7a92b8c4868882b9"
    },
    {
      "exists": true,
      "name": "sidecar_join_map",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
      "sha256": "60ebcd0c75adc9836f79aaeb9ff53c93cd45e8947823cafc426ff6bab5aece4b"
    },
    {
      "exists": true,
      "name": "sidecar_noleak",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
      "sha256": "8f9d84082004c6ce2d41463f1c2afd71e5179a26e9f59fda2a3359521d6ac109"
    },
    {
      "exists": true,
      "name": "sidecar_packet_json",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json",
      "sha256": "ac3b3765ed605957a54d7d06f079a076d9d7c8b04a14e44f1c9f5e92f86fd2b6"
    },
    {
      "exists": true,
      "name": "sidecar_packet_jsonl",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
      "sha256": "1c522252249cb6cf045ac83f5a3b4251615a10d538d88965066fa7c9b289803c"
    },
    {
      "exists": true,
      "name": "sidecar_proposal",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
      "sha256": "31e3a3e008d17a52d2b1545c50f0c8739dab0b1701af90eb3e2ee2fc94223a1a"
    },
    {
      "exists": true,
      "name": "sidecar_search_hash",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
      "sha256": "9b6739b76c3c7c61434da15c502b2d0f6cfa23d1b1a8d76baecb596010e4c744"
    }
  ],
  "generated_at_utc": "2026-05-08T04:41:16Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quote_path_asof_checks": [
    {
      "decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-04T11:15:00Z",
      "path_first_timestamp_utc": "2026-05-04T07:15:00.222000Z",
      "path_last_timestamp_utc": "2026-05-04T11:14:59.241000Z",
      "path_row_count": 40639,
      "path_start_utc": "2026-05-04T07:15:00Z",
      "quote_age_ms": 76,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-04T07:14:59.924000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_index": 1,
      "status": "PASS",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-04T11:15:00Z",
      "path_first_timestamp_utc": "2026-05-04T07:15:00.222000Z",
      "path_last_timestamp_utc": "2026-05-04T11:14:59.241000Z",
      "path_row_count": 40639,
      "path_start_utc": "2026-05-04T07:15:00Z",
      "quote_age_ms": 76,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-04T07:14:59.924000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_index": 2,
      "status": "PASS",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision_asof_utc": "2026-05-05T16:30:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T20:30:00Z",
      "path_first_timestamp_utc": "2026-05-05T16:30:00.343000Z",
      "path_last_timestamp_utc": "2026-05-05T20:29:59.521000Z",
      "path_row_count": 23608,
      "path_start_utc": "2026-05-05T16:30:00Z",
      "quote_age_ms": 158,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:29:59.842000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_index": 3,
      "status": "PASS",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision_asof_utc": "2026-05-05T16:30:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T20:30:00Z",
      "path_first_timestamp_utc": "2026-05-05T16:30:00.343000Z",
      "path_last_timestamp_utc": "2026-05-05T20:29:59.521000Z",
      "path_row_count": 23608,
      "path_start_utc": "2026-05-05T16:30:00Z",
      "quote_age_ms": 158,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:29:59.842000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_index": 4,
      "status": "PASS",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision_asof_utc": "2026-05-05T16:45:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T20:45:00Z",
      "path_first_timestamp_utc": "2026-05-05T16:45:00.082000Z",
      "path_last_timestamp_utc": "2026-05-05T20:44:59.986000Z",
      "path_row_count": 22291,
      "path_start_utc": "2026-05-05T16:45:00Z",
      "quote_age_ms": 21,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:44:59.979000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_index": 5,
      "status": "PASS",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision_asof_utc": "2026-05-05T16:45:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T20:45:00Z",
      "path_first_timestamp_utc": "2026-05-05T16:45:00.082000Z",
      "path_last_timestamp_utc": "2026-05-05T20:44:59.986000Z",
      "path_row_count": 22291,
      "path_start_utc": "2026-05-05T16:45:00Z",
      "quote_age_ms": 21,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:44:59.979000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_index": 6,
      "status": "PASS",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "decision_asof_utc": "2026-05-05T17:00:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T21:00:00Z",
      "path_first_timestamp_utc": "2026-05-05T17:00:00.077000Z",
      "path_last_timestamp_utc": "2026-05-05T20:59:59.174000Z",
      "path_row_count": 20819,
      "path_start_utc": "2026-05-05T17:00:00Z",
      "quote_age_ms": 130,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:59:59.870000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_index": 7,
      "status": "PASS",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "decision_asof_utc": "2026-05-05T17:00:00+00:00",
      "path_asof_status": "PASS",
      "path_end_utc": "2026-05-05T21:00:00Z",
      "path_first_timestamp_utc": "2026-05-05T17:00:00.077000Z",
      "path_last_timestamp_utc": "2026-05-05T20:59:59.174000Z",
      "path_row_count": 20819,
      "path_start_utc": "2026-05-05T17:00:00Z",
      "quote_age_ms": 130,
      "quote_asof_status": "PASS",
      "quote_path_hash_match_status": "PASS",
      "quote_timestamp_utc": "2026-05-05T16:59:59.870000+00:00",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_index": 8,
      "status": "PASS",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    }
  ],
  "quote_path_asof_summary": {
    "fail_count": 0,
    "pass_count": 8,
    "rows_checked": 8
  },
  "row_join_checks": [
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_index": 1,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a",
      "source_row_sha256": "7c3093be6f686cdd2467cc6b46e5f19fc7cea7a82e71b5fdefab0d747e2bf197",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_index": 2,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
      "source_row_sha256": "340b2a33e6bb100cc893a48cbdac13c69346ec2aabe82dbf657a647453eb7202",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_index": 3,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "source_row_sha256": "3b28e2322f1d5acdf4486212be47e4a3773d3fdcf66bfb9771ea720bedb337a2",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_index": 4,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "source_row_sha256": "b0fc02e32f7aa38375194255963fc58275b09dfdaa152573e23d8388a0b5a3ac",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_index": 5,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "source_row_sha256": "fae5fe3b8657c5adca8244a7a0abf763be6e3897e0475114a046528404b97568",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_index": 6,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "source_row_sha256": "91668476f9891c7dcddf653c9f8790580f4c63d0a340c35a34e0bdc178b97058",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_index": 7,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
      "source_row_sha256": "fdb3c2bf53decfcde7ccbfe37b0bd45514fd9de56b7e48bbc353d22f72107d7f",
      "status": "PASS"
    },
    {
      "cnr_source_matches": 1,
      "g12_ready_matches": 1,
      "g6_input_record_matches": 1,
      "matrix_source_matches": 1,
      "otx_record_matches": 1,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_index": 8,
      "sidecar_row_hash_status": "PASS",
      "sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "source_row_sha256": "ee3cc4552784d174f54e8da4f959994b9c263dec96984ee039df218d3e0c9e88",
      "status": "PASS"
    }
  ],
  "row_join_summary": {
    "duplicate_group_only_join_policy": "REJECTED_AS_INSUFFICIENT_WHEN_AMBIGUOUS",
    "fail_count": 0,
    "join_method": "source_row_sha256_for_CNR_G12_matrix_plus_record_id_for_OTX_G6",
    "pass_count": 8,
    "sidecar_rows_checked": 8
  },
  "schema_version": "g12_cnr061_sidecar_reaudit_v1",
  "sidecar_source_evidence_recompute": [
    {
      "actual_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "exists": true,
      "expected_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "join_role": "quote_and_path_tick_source",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
      "source_name": "TICK_PARQUET_SOURCE",
      "status": "PASS"
    },
    {
      "actual_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "exists": true,
      "expected_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "join_role": "quote_and_path_tick_source",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "source_name": "TICK_PARQUET_SOURCE",
      "status": "PASS"
    },
    {
      "actual_sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
      "exists": true,
      "expected_sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
      "join_role": "geometry_residual_control_source",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
      "source_name": "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX",
      "status": "PASS"
    },
    {
      "actual_sha256": "883525dae5981227ffcddc0e819bb269585367c315b8568975d214212239c7bb",
      "exists": true,
      "expected_sha256": "883525dae5981227ffcddc0e819bb269585367c315b8568975d214212239c7bb",
      "join_role": "geometry_and_quote_source_row",
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
      "source_name": "CNR_SOURCE_FIELD_PACKET_ROWS",
      "status": "PASS"
    },
    {
      "actual_sha256": "ef9feef8508c069eac6328fcfd450476bb76862c25f3ec8a7433a1307114e499",
      "exists": true,
      "expected_sha256": "ef9feef8508c069eac6328fcfd450476bb76862c25f3ec8a7433a1307114e499",
      "join_role": "accepted_input_row_gate",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json",
      "source_name": "G12_CNR_READY_ROW_SHORTLIST",
      "status": "PASS"
    },
    {
      "actual_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
      "exists": true,
      "expected_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
      "join_role": "original_entry_sl_tp_source",
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "source_name": "OTG0_PKT061_G6_INPUT_PACKET",
      "status": "PASS"
    },
    {
      "actual_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
      "exists": true,
      "expected_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
      "join_role": "decision_quote_and_ordered_path_source",
      "path": "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
      "source_name": "OTX_G6_REBUILT_PACKET_PROPOSALS",
      "status": "PASS"
    }
  ],
  "sidecar_source_evidence_summary": {
    "mismatch_count": 0,
    "unique_sources_checked": 7
  },
  "upstream_source_search_ledger_recompute": {
    "mutable_context_or_prompt_mismatch_count": 3,
    "mutable_context_or_prompt_mismatches": [
      {
        "actual_sha256": "92e7d73b7d050d8c7ebef7815685f97c0381d2080d8c6fa964fbad02a39c52d3",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "5f3f6996e2b4ab4c6f0de58d4f132f83d86b491af8a96cfade826fad7d08a581",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_GOAL_PROMPT_2026-05-08.md",
        "role": "goal_prompt",
        "status": "MISMATCH"
      },
      {
        "actual_sha256": "39b1d1e896f3b6121cf9aafe88e98d00ec9317aac80781adf78e3fe614601d42",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "c543d3f8f2add1d306589f63cb500a1b846d9834aa54289261c2e25f3e2fc7d6",
        "path": ".context/LIVE_STATE.md",
        "role": "live_state",
        "status": "MISMATCH"
      },
      {
        "actual_sha256": "38a4084d8d2e41f869aa673dc47b25cc7667efa3aa10ec1190c9308eb32364ab",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "ee7b85a96948140ea0fd820a9ba0730c81aa1e9578e282f19459ac2c2f7472d2",
        "path": ".context/00_core/research_current_state.md",
        "role": "research_current_state",
        "status": "MISMATCH"
      }
    ],
    "rows": [
      {
        "actual_sha256": "92e7d73b7d050d8c7ebef7815685f97c0381d2080d8c6fa964fbad02a39c52d3",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "5f3f6996e2b4ab4c6f0de58d4f132f83d86b491af8a96cfade826fad7d08a581",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_GOAL_PROMPT_2026-05-08.md",
        "role": "goal_prompt",
        "status": "MISMATCH"
      },
      {
        "actual_sha256": "39b1d1e896f3b6121cf9aafe88e98d00ec9317aac80781adf78e3fe614601d42",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "c543d3f8f2add1d306589f63cb500a1b846d9834aa54289261c2e25f3e2fc7d6",
        "path": ".context/LIVE_STATE.md",
        "role": "live_state",
        "status": "MISMATCH"
      },
      {
        "actual_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
        "path": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        "role": "latest_handoff",
        "status": "PASS"
      },
      {
        "actual_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
        "path": ".context/00_core/quick_reference_card.md",
        "role": "quick_reference",
        "status": "PASS"
      },
      {
        "actual_sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
        "path": ".context/00_core/research_operating_doctrine.md",
        "role": "research_doctrine",
        "status": "PASS"
      },
      {
        "actual_sha256": "38a4084d8d2e41f869aa673dc47b25cc7667efa3aa10ec1190c9308eb32364ab",
        "classification": "MUTABLE_CONTEXT_OR_PROMPT",
        "exists": true,
        "expected_sha256": "ee7b85a96948140ea0fd820a9ba0730c81aa1e9578e282f19459ac2c2f7472d2",
        "path": ".context/00_core/research_current_state.md",
        "role": "research_current_state",
        "status": "MISMATCH"
      },
      {
        "actual_sha256": "d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994",
        "path": ".context/00_core/goal_session_research_discipline.md",
        "role": "goal_discipline",
        "status": "PASS"
      },
      {
        "actual_sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
        "path": ".context/00_core/local_heavy_data_inventory.md",
        "role": "local_heavy_inventory",
        "status": "PASS"
      },
      {
        "actual_sha256": "cc819f69aea3321a6fd26ec05dba6683c2d06454ea1dce7131812de2cc3516e1",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "cc819f69aea3321a6fd26ec05dba6683c2d06454ea1dce7131812de2cc3516e1",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
        "role": "cnr_blocker_decision",
        "status": "PASS"
      },
      {
        "actual_sha256": "b9bd5b6af459b6c7c2e8e9f177db479330625baf9c244727df52b1d08c4537ce",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "b9bd5b6af459b6c7c2e8e9f177db479330625baf9c244727df52b1d08c4537ce",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
        "role": "cnr_blocker_decision_md",
        "status": "PASS"
      },
      {
        "actual_sha256": "78759e1606d00fca76a173259c6ce838847c91dae77443d4dd3dc62a2f6a9e5d",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "78759e1606d00fca76a173259c6ce838847c91dae77443d4dd3dc62a2f6a9e5d",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
        "role": "cnr_prior_search",
        "status": "PASS"
      },
      {
        "actual_sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
        "role": "cnr_matrix",
        "status": "PASS"
      },
      {
        "actual_sha256": "883525dae5981227ffcddc0e819bb269585367c315b8568975d214212239c7bb",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "883525dae5981227ffcddc0e819bb269585367c315b8568975d214212239c7bb",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
        "role": "cnr_rows",
        "status": "PASS"
      },
      {
        "actual_sha256": "bfe31c2fb87a19b0139431e0eed5cb1926afffe6986ab395f56cf6e3d2c3b6e3",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "bfe31c2fb87a19b0139431e0eed5cb1926afffe6986ab395f56cf6e3d2c3b6e3",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json",
        "role": "cnr_manifest",
        "status": "PASS"
      },
      {
        "actual_sha256": "ef9feef8508c069eac6328fcfd450476bb76862c25f3ec8a7433a1307114e499",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "ef9feef8508c069eac6328fcfd450476bb76862c25f3ec8a7433a1307114e499",
        "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json",
        "role": "g12_ready",
        "status": "PASS"
      },
      {
        "actual_sha256": "f56966f12e59ddd6ecd1a694beb9d6f642ac3d75342895ddc075d9b7c7eb5de4",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "f56966f12e59ddd6ecd1a694beb9d6f642ac3d75342895ddc075d9b7c7eb5de4",
        "path": "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json",
        "role": "g12_cnr_blockers",
        "status": "PASS"
      },
      {
        "actual_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
        "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "role": "g6_input_packet",
        "status": "PASS"
      },
      {
        "actual_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
        "path": "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
        "role": "otx_proposals",
        "status": "PASS"
      },
      {
        "actual_sha256": "4fcc804ac444cac0afc9ee2112587d4675df76228c06fec54c77fc2ccaf0664e",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "4fcc804ac444cac0afc9ee2112587d4675df76228c06fec54c77fc2ccaf0664e",
        "path": "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json",
        "role": "g12_otx_source_hash",
        "status": "PASS"
      },
      {
        "actual_sha256": "d5a67175ab1da11941d29440e4b490b12648a3da60cd5c0bc45d4ebec7e7bc01",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "d5a67175ab1da11941d29440e4b490b12648a3da60cd5c0bc45d4ebec7e7bc01",
        "path": "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
        "role": "otr061_proposal",
        "status": "PASS"
      },
      {
        "actual_sha256": "3de2d8b35d272705df241a4bbc38ab2534273b5e4b6e4d6bdccc4353182e3b21",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "3de2d8b35d272705df241a4bbc38ab2534273b5e4b6e4d6bdccc4353182e3b21",
        "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
        "role": "g12_oti5_otr061_audit",
        "status": "PASS"
      },
      {
        "actual_sha256": "dbcc7db56b303a400dea8bc2d5146bcb0c4234f346850cfb4d273aec03f46129",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "dbcc7db56b303a400dea8bc2d5146bcb0c4234f346850cfb4d273aec03f46129",
        "path": "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_2026-05-08.json",
        "role": "g12_oti7_blocker_map",
        "status": "PASS"
      },
      {
        "actual_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
        "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
        "role": "sidecar_row_source_evidence",
        "status": "PASS"
      },
      {
        "actual_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
        "classification": "STRICT_ROW_OR_CONTROL_SOURCE",
        "exists": true,
        "expected_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
        "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
        "role": "sidecar_row_source_evidence",
        "status": "PASS"
      }
    ],
    "source_file_count": 24,
    "status": "PASS_STRICT_ROW_SOURCES",
    "strict_failures": [],
    "strict_row_or_control_source_mismatch_count": 0
  },
  "validation_safe": false
}
```
