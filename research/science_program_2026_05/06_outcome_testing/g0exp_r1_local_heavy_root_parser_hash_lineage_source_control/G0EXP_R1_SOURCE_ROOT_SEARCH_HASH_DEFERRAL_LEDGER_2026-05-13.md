# G0EXP R1 Source Root Search And Hash Deferral Ledger

- **route_id:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL`
- **evidence_class:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- Present roots: `19` / `19`.
- Metadata-only file count: `118563`.
- Raw/heavy deferral records: `206`.

```json
{
  "absent_root_count": 0,
  "artifact_family": "source_root_search_and_hash_deferral_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY",
  "exact_future_rehash_requirement": "A future route may hash a specific raw/heavy file read-only only after it is selected as a consumed source. The raw file remains uncommitted; record absolute path, size, mtime, sha256, parser, and as-of rule.",
  "generated_at_utc": "2026-05-13T02:51:56Z",
  "hash_deferral_count": 206,
  "hash_deferral_records": [
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\feature_matrix.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\feature_matrix.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".depth"
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 3047
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 254625
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\canary_restart_governance_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 8453
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 8375704
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_registry_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 478526
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_ledger.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 741802
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_budget_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_budget_ledger.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 4581
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\es_mes_preregistration_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\es_mes_preregistration_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 86848
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\exit_management_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\exit_management_shadow_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1441477
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\external_source_blocker_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1167576
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 50673
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\lto_blocked_lane_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\lto_blocked_lane_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 2375
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\ml_shadow_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 207367
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 230299
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\notification_queue_dead_zone_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\notification_queue_dead_zone_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 40278
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\orderflow_primitives_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\orderflow_primitives_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1092750
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\proxy_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\proxy_blocker_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 189364
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\session_volatility_sweep_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\session_volatility_sweep_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 45777
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_hardening_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_hardening_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1470770
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 3614239
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 8188
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_fpb_source_audit_final\\test_parse_scid_independent_re0\\TEST.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_fpb_source_audit_final\\test_parse_scid_independent_re0\\TEST.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_hard_floor_requires_previ0\\6BM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_hard_floor_requires_previ0\\6BM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_raw_byte_rehash_uses_mani0\\NQM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_raw_byte_rehash_uses_mani0\\NQM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_selected_hash_overlap_blo0\\YMM26-CBOT.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_selected_hash_overlap_blo0\\YMM26-CBOT.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_0\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 567
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_1\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_1\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 567
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_2\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_2\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 567
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_canary_restart_governance1\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_canary_restart_governance1\\shadow_logs\\canary_restart_governance_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1620
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_path_contract_a0\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_path_contract_a0\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1743
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra0\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra0\\shadow_logs\\candidate_registry_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 2244
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra2\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra2\\shadow_logs\\candidate_registry_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 2250
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1241
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 6741
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1217
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1094
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1554
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-04.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-04.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-05.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-05.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-06.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-07.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-07.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-09.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-09.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-10.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-10.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-11.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-11.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-12.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-12.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 255834
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 8453
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 8404652
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 480776
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 744781
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 4581
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 86843
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1443533
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 1200729
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 53064
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 2372
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 213360
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl.lock",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 0
    },
    {
      "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 235918
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\lto002_debug\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\lto002_debug\\shadow_logs\\candidate_registry_audit.jsonl",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 2196
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".gz"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\feature_matrix.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\feature_matrix.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".parquet"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".depth"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-02_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-02_delayed.depth",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".depth"
    },
    {
      "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv read-only in a source-control lane if it becomes a consumed source.",
      "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
      "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
      "size_bytes": 3047
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6AM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6AM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6BM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6CM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6CM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6EM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6JM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6JM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6SM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\6SM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\AAPL.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\AAPL.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\AMZN-NQTV.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\AMZN-NQTV.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\CLM26-NYMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\CLM26-NYMEX.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\ESM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\ESM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\EURUSD.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\EURUSD.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\GCM26-COMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\M2KM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\M2KM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MCLM26-NYMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MCLM26-NYMEX.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MESM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MESM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MESU25-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MESU25-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MGCM26-COMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MGCM26-COMEX.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MNQM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MNQM26-CME.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MYMM26-CBOT.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\SierraChart\\Data\\MYMM26-CBOT.scid",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".scid"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    },
    {
      "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
      "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
      "reason": "Raw/heavy market data blob is not committed or copied by this route.",
      "suffix": ".xlsx"
    }
  ],
  "hashed_control_sample_count": 79,
  "hashed_control_samples": [
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
      "sha256": "ca93cc0d58542234f84ab20adcd4997b90ed0fa6f6cbb0521ea9da08cb8525d3",
      "size_bytes": 15709
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\config\\shadow_observer_registry.yaml",
      "sha256": "1b8000c5283edd48f7f68d7d1b521d76a080f6f531d92cced9527f3b898733c0",
      "size_bytes": 5793
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
      "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
      "size_bytes": 5253
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
      "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
      "size_bytes": 5248
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
      "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
      "size_bytes": 89398
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
      "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
      "size_bytes": 5263
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
      "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
      "size_bytes": 5268
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
      "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
      "size_bytes": 5292
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
      "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
      "size_bytes": 5330
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\operations\\data_manifest.md",
      "sha256": "0c6f557574b8b56e2010b69cc779d6485fcf0a7509e462e381537b61cec56f89",
      "size_bytes": 7657
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\cascade_prompt_status_2026-04-25.md",
      "sha256": "83b972d77aeef7d8fdcc37fdef2acb9709e73bd57f06e9549aab02873a26ebba",
      "size_bytes": 14843
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
      "sha256": "998fad54e7e0934a282106ec40b55dbdb152006c18a52dc36d63769306f1ade4",
      "size_bytes": 98303
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
      "sha256": "c2bb6094f91557e179c9d4fb21c88ec3f419313a430d1fc3af46fd14cbb1ba33",
      "size_bytes": 3375
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
      "sha256": "319b3bcf1f1ebeda390eb9ffad9f60f88e652dd671a58dd575da07e906ea3cd2",
      "size_bytes": 97675
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
      "sha256": "a9349666f9b6886f1558911a6d5651210762504459ecc3de54219b2cca324ce7",
      "size_bytes": 3269
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
      "sha256": "663b05a0581dda519a4e3254a2d1b3273e21d5f87a4a2c2aa3ccc01ccb8598a7",
      "size_bytes": 275351
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
      "sha256": "40efc5d4f7b4cf0dfa6d82a372c1e10aad69a381be062fa6908ef6024b134616",
      "size_bytes": 4616
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
      "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
      "size_bytes": 5253
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
      "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
      "size_bytes": 5248
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
      "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
      "size_bytes": 89398
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
      "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
      "size_bytes": 5263
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
      "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
      "size_bytes": 5268
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
      "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
      "size_bytes": 5292
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
      "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
      "size_bytes": 5330
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
      "sha256": "63b2fadaf818bf4dc1b604ec6efce12dd139dd1087b280898de35190f4d48542",
      "size_bytes": 15549
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\codex_probe_eurusd_20260415\\manifest.json",
      "sha256": "e6111e723abde9bd997ac408d63b1515f2479d832a69ca5464391312e34f5ad7",
      "size_bytes": 1858
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_candidate_gap_20260501\\manifest.json",
      "sha256": "648fe634b4d9bdfdc334e1bd28b8dad9f088700fcd14db6066464c4cac238a9e",
      "size_bytes": 3267
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m15_2022_2026_fn_chunked_v1\\manifest.json",
      "sha256": "910ad094abff1dffe1c994aef3512f8e2f0be32debb131b40c01777c58a9c301",
      "size_bytes": 5457
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\manifest.json",
      "sha256": "e1fed7352439b8a8e240ffeaf42c6f2601c2ef5d79c092fd4ef8198b807807ed",
      "size_bytes": 18542
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\manifest.json",
      "sha256": "39467b736e1056e93e850bfdd93ada3f32aec112c4e423338aea34801bd1b9e4",
      "size_bytes": 10191
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_20220501\\manifest.json",
      "sha256": "b3b2b516a547051b2012b91ab62b2d2649fed0f025e254d5a9e1eda786266ba0",
      "size_bytes": 1971
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_after_maxbars\\manifest.json",
      "sha256": "06fb2e21244c39b56682e8b6e89b6b36714f9f301545e8714490c57164c23b3a",
      "size_bytes": 1993
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\manifest.json",
      "sha256": "a4cec6442c7608635159dddd0d98abe5cd7ca659b68d31271c6db87ed4a33763",
      "size_bytes": 27120
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\manifest.json",
      "sha256": "d1979df60412ce6c01426e6546ec335dcaf7d4fed55784bc6129786fb4cae9a5",
      "size_bytes": 22191
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
      "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
      "size_bytes": 5253
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
      "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
      "size_bytes": 5248
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
      "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
      "size_bytes": 89398
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
      "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
      "size_bytes": 5263
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
      "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
      "size_bytes": 5268
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
      "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
      "size_bytes": 5292
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
      "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
      "size_bytes": 5330
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_recovery\\live_mechanical_lfs_repair_manifest_20260511T034433Z.json",
      "sha256": "98b612f7a61872ce83cf590564c456793bfd83abef3f06f819f9a616883972ed",
      "size_bytes": 874
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
      "sha256": "ca93cc0d58542234f84ab20adcd4997b90ed0fa6f6cbb0521ea9da08cb8525d3",
      "size_bytes": 15709
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\config\\shadow_observer_registry.yaml",
      "sha256": "1b8000c5283edd48f7f68d7d1b521d76a080f6f531d92cced9527f3b898733c0",
      "size_bytes": 5793
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
      "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
      "size_bytes": 5253
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
      "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
      "size_bytes": 5248
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
      "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
      "size_bytes": 89398
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
      "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
      "size_bytes": 5263
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
      "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
      "size_bytes": 5268
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
      "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
      "size_bytes": 5292
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
      "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
      "size_bytes": 5330
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\operations\\data_manifest.md",
      "sha256": "0c6f557574b8b56e2010b69cc779d6485fcf0a7509e462e381537b61cec56f89",
      "size_bytes": 7657
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\cascade_prompt_status_2026-04-25.md",
      "sha256": "83b972d77aeef7d8fdcc37fdef2acb9709e73bd57f06e9549aab02873a26ebba",
      "size_bytes": 14843
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
      "sha256": "998fad54e7e0934a282106ec40b55dbdb152006c18a52dc36d63769306f1ade4",
      "size_bytes": 98303
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
      "sha256": "c2bb6094f91557e179c9d4fb21c88ec3f419313a430d1fc3af46fd14cbb1ba33",
      "size_bytes": 3375
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
      "sha256": "319b3bcf1f1ebeda390eb9ffad9f60f88e652dd671a58dd575da07e906ea3cd2",
      "size_bytes": 97675
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
      "sha256": "a9349666f9b6886f1558911a6d5651210762504459ecc3de54219b2cca324ce7",
      "size_bytes": 3269
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
      "sha256": "663b05a0581dda519a4e3254a2d1b3273e21d5f87a4a2c2aa3ccc01ccb8598a7",
      "size_bytes": 275351
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
      "sha256": "40efc5d4f7b4cf0dfa6d82a372c1e10aad69a381be062fa6908ef6024b134616",
      "size_bytes": 4616
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472
    },
    {
      "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245
    }
  ],
  "head_at_build": "3ab07d464082",
  "live_effect": false,
  "no_raw_market_blob_content_copied": true,
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
  "present_root_count": 19,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "root_count": 19,
  "route_id": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
  "scanned_roots": [
    {
      "dir_count": 756,
      "errors": [
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'"
      ],
      "exists": true,
      "extension_counts": {
        ".bak": 3,
        ".bat": 2,
        ".csv": 615,
        ".depth": 2,
        ".html": 148,
        ".jpeg": 42,
        ".jpg": 2,
        ".js": 1,
        ".json": 7002,
        ".jsonl": 415,
        ".jsonl.gz": 8,
        ".lgb": 18,
        ".log": 155,
        ".md": 3943,
        ".mq5": 1,
        ".parquet": 16,
        ".patch": 1,
        ".pdf": 9,
        ".png": 128,
        ".ps1": 3,
        ".py": 1703,
        ".sh": 11,
        ".template": 2,
        ".toml": 1,
        ".txt": 218,
        ".vbs": 2,
        ".xml": 3,
        ".yaml": 417,
        "[no_ext]": 35
      },
      "file_count": 14906,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\feature_matrix.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\feature_matrix.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".depth"
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 3047
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "sha256": "ca93cc0d58542234f84ab20adcd4997b90ed0fa6f6cbb0521ea9da08cb8525d3",
          "size_bytes": 15709
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\config\\shadow_observer_registry.yaml",
          "sha256": "1b8000c5283edd48f7f68d7d1b521d76a080f6f531d92cced9527f3b898733c0",
          "size_bytes": 5793
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
          "size_bytes": 5253
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
          "size_bytes": 5248
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
          "size_bytes": 89398
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
          "size_bytes": 5263
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
          "size_bytes": 5268
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
          "size_bytes": 5292
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
          "size_bytes": 5330
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\operations\\data_manifest.md",
          "sha256": "0c6f557574b8b56e2010b69cc779d6485fcf0a7509e462e381537b61cec56f89",
          "size_bytes": 7657
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\cascade_prompt_status_2026-04-25.md",
          "sha256": "83b972d77aeef7d8fdcc37fdef2acb9709e73bd57f06e9549aab02873a26ebba",
          "size_bytes": 14843
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
          "sha256": "998fad54e7e0934a282106ec40b55dbdb152006c18a52dc36d63769306f1ade4",
          "size_bytes": 98303
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
          "sha256": "c2bb6094f91557e179c9d4fb21c88ec3f419313a430d1fc3af46fd14cbb1ba33",
          "size_bytes": 3375
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
          "sha256": "319b3bcf1f1ebeda390eb9ffad9f60f88e652dd671a58dd575da07e906ea3cd2",
          "size_bytes": 97675
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
          "sha256": "a9349666f9b6886f1558911a6d5651210762504459ecc3de54219b2cca324ce7",
          "size_bytes": 3269
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
          "sha256": "663b05a0581dda519a4e3254a2d1b3273e21d5f87a4a2c2aa3ccc01ccb8598a7",
          "size_bytes": 275351
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
          "sha256": "40efc5d4f7b4cf0dfa6d82a372c1e10aad69a381be062fa6908ef6024b134616",
          "size_bytes": 4616
        }
      ],
      "is_dir": true,
      "label": "current_worktree",
      "manifest_control_candidate_count": 2060,
      "market_data_like_count": 641,
      "max_depth": 7,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 618,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE",
      "raw_market_blob_count": 26,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "size_bytes": 15709
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\config\\shadow_observer_registry.yaml",
          "size_bytes": 5793
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "size_bytes": 5253
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "size_bytes": 5248
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "size_bytes": 89398
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "size_bytes": 5263
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "size_bytes": 5268
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "size_bytes": 5292
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "size_bytes": 5330
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\operations\\data_manifest.md",
          "size_bytes": 7657
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\cascade_prompt_status_2026-04-25.md",
          "size_bytes": 14843
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
          "size_bytes": 3047
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
          "size_bytes": 98303
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
          "size_bytes": 3375
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
          "size_bytes": 97675
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
          "size_bytes": 3269
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
          "size_bytes": 275351
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
          "size_bytes": 4616
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.DS_Store",
          "size_bytes": 24580
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.git",
          "size_bytes": 78
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.gitattributes",
          "size_bytes": 939
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\.gitignore",
          "size_bytes": 8519
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\AGENTS.md",
          "size_bytes": 37009
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\asba.txt",
          "size_bytes": 354
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\autocorrelation_baselines.md",
          "size_bytes": 2055
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\batch_backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\CEO_DIRECTIVE_COMPLETION_REPORT.md",
          "size_bytes": 1662
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\CLAUDE.md",
          "size_bytes": 33556
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\CORRECTED_INTELLIGENCE_BRIEF_APRIL7.md",
          "size_bytes": 5032
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\DATA_VERIFICATION_MATRIX.md",
          "size_bytes": 11668
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\decomposition_raw_results.json",
          "size_bytes": 9167
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\decomposition_real_mso_test.md",
          "size_bytes": 6466
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\defaults_and_tests_audit.md",
          "size_bytes": 11942
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\demo_infrastructure.py",
          "size_bytes": 6144
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\devils_advocate_test_results.md",
          "size_bytes": 4677
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\DIVERGENCE_SAMPLER_REPORT.md",
          "size_bytes": 8642
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\dst_effect_analysis.md",
          "size_bytes": 2956
        }
      ],
      "sample_parser_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\knowledge_base_backtest\\analysis\\trade_capture_pressure_test_runner.py",
          "size_bytes": 43435
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\podcast_pipeline\\test_results\\audit_h34_calendar.py",
          "size_bytes": 2935
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\podcast_pipeline\\verification\\verify_batch_b.py",
          "size_bytes": 16326
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\a4_trending_bull_replay_2026-04-28\\build_realized_r_join.py",
          "size_bytes": 6653
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\academic_pipeline\\scripts\\q_1_1_mi_audit.py",
          "size_bytes": 32804
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase1\\_zeta_scratch\\04_visual_mso_audit.py",
          "size_bytes": 10111
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase1\\_zeta_scratch\\07_market_state_algo_verify.py",
          "size_bytes": 5573
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T1_scratch\\01_verify_gap_signature.py",
          "size_bytes": 4837
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\verify_xauusd_details.py",
          "size_bytes": 4711
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\directional_concentration_audit_2026-04-24\\scripts\\structure_stickiness.py",
          "size_bytes": 5344
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\halluc_4_cross_instrument_context\\build_audit.py",
          "size_bytes": 16309
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\halluc_4_cross_instrument_context\\build_combined_audit.py",
          "size_bytes": 5079
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\lira_ab_deep_forensic\\red_team\\red_team_verify.py",
          "size_bytes": 27334
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\audit\\_audit_run.py",
          "size_bytes": 19973
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\forensics\\2026-04-29\\_agent_k1_verify.py",
          "size_bytes": 32566
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\build_scout_matrix.py",
          "size_bytes": 27373
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scripts\\build_catalog_v2.py",
          "size_bytes": 5774
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scripts\\_build_regime_catalog.py",
          "size_bytes": 12467
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scripts\\features\\_build_liquidity_catalog.py",
          "size_bytes": 5942
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scripts\\features\\_build_structure_catalog.py",
          "size_bytes": 16126
        }
      ],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
          "size_bytes": 670
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
          "size_bytes": 2683
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
          "size_bytes": 5326
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
          "size_bytes": 742597
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
          "size_bytes": 656740
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
          "size_bytes": 119899
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\ml_program\\scout\\feature_matrix.parquet",
          "size_bytes": 2739471
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
          "size_bytes": 274409
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
          "size_bytes": 338699
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
          "size_bytes": 337507
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
          "size_bytes": 338251
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
          "size_bytes": 306548
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
          "size_bytes": 302894
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
          "size_bytes": 306765
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
          "size_bytes": 249227
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
          "size_bytes": 16603
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "size_bytes": 2209369
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "size_bytes": 2045401
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
          "size_bytes": 1584013
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
          "size_bytes": 160
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_WITH_ERRORS",
      "total_bytes": 3948991570,
      "truncated": false
    },
    {
      "dir_count": 32,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".csv": 305,
        ".json": 19,
        ".jsonl": 13,
        ".md": 2
      },
      "file_count": 339,
      "hash_deferral_records": [],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
          "size_bytes": 5253
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
          "size_bytes": 5248
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
          "size_bytes": 89398
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
          "size_bytes": 5263
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
          "size_bytes": 5268
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
          "size_bytes": 5292
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
          "size_bytes": 5330
        }
      ],
      "is_dir": true,
      "label": "current_worktree_data",
      "manifest_control_candidate_count": 7,
      "market_data_like_count": 305,
      "max_depth": 7,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "size_bytes": 5253
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "size_bytes": 5248
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "size_bytes": 89398
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "size_bytes": 5263
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "size_bytes": 5268
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "size_bytes": 5292
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "size_bytes": 5330
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\DXY_D1.csv",
          "size_bytes": 20017
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\economic_calendar.csv",
          "size_bytes": 1602
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\EURUSD_D1.csv",
          "size_bytes": 30108
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\EURUSD_H1.csv",
          "size_bytes": 828266
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\EURUSD_H4.csv",
          "size_bytes": 209541
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\EURUSD_M15.csv",
          "size_bytes": 3273362
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\EURUSD_M5.csv",
          "size_bytes": 5291443
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\GBPUSD_D1.csv",
          "size_bytes": 177741
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\GBPUSD_H1.csv",
          "size_bytes": 1165745
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\GBPUSD_H4.csv",
          "size_bytes": 580221
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\GBPUSD_M15.csv",
          "size_bytes": 2903066
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\GBPUSD_M5.csv",
          "size_bytes": 19603
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\NAS100_D1.csv",
          "size_bytes": 28780
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\NAS100_H1.csv",
          "size_bytes": 744327
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\NAS100_H4.csv",
          "size_bytes": 197086
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\NAS100_M15.csv",
          "size_bytes": 2934918
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\NAS100_M5.csv",
          "size_bytes": 5301737
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\news_calendar.json",
          "size_bytes": 4013
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\XAGUSD_D1.csv",
          "size_bytes": 26899
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\XAGUSD_H1.csv",
          "size_bytes": 723400
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 182630663,
      "truncated": false
    },
    {
      "dir_count": 0,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".md": 1
      },
      "file_count": 1,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "current_worktree_data_ticks",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 0,
      "max_depth": 4,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\ticks",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\ticks\\README.md",
          "size_bytes": 5376
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 5376,
      "truncated": false
    },
    {
      "dir_count": 14,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".json": 9,
        ".jsonl": 9
      },
      "file_count": 18,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "current_worktree_data_external",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 0,
      "max_depth": 6,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
          "size_bytes": 91368
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
          "size_bytes": 28052
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
          "size_bytes": 97535
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
          "size_bytes": 28042
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_events_20260503T202913Z.jsonl",
          "size_bytes": 77834
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_replay_20260503T202915Z.json",
          "size_bytes": 28101
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
          "size_bytes": 73638
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205252Z.json",
          "size_bytes": 28733
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T205339Z.json",
          "size_bytes": 104394
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T205337Z.jsonl",
          "size_bytes": 63942
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T204511Z.jsonl",
          "size_bytes": 77104
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204512Z.json",
          "size_bytes": 28824
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204612Z.json",
          "size_bytes": 113667
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204606Z.jsonl",
          "size_bytes": 336479
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_events_20260503T204727Z.jsonl",
          "size_bytes": 51679
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204728Z.json",
          "size_bytes": 28788
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204801Z.json",
          "size_bytes": 104112
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204759Z.jsonl",
          "size_bytes": 64470
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 1426762,
      "truncated": false
    },
    {
      "dir_count": 1,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bak": 2,
        ".csv": 4,
        ".json": 10,
        ".jsonl": 100,
        ".jsonl.gz": 5
      },
      "file_count": 121,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 254625
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\canary_restart_governance_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 8453
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 8375704
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_registry_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 478526
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_ledger.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 741802
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_budget_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_budget_ledger.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 4581
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\es_mes_preregistration_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\es_mes_preregistration_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 86848
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\exit_management_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\exit_management_shadow_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1441477
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\external_source_blocker_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1167576
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 50673
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\lto_blocked_lane_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\lto_blocked_lane_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 2375
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\ml_shadow_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 207367
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 230299
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\notification_queue_dead_zone_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\notification_queue_dead_zone_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 40278
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\orderflow_primitives_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\orderflow_primitives_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1092750
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\proxy_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\proxy_blocker_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 189364
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\session_volatility_sweep_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\session_volatility_sweep_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 45777
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_hardening_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_hardening_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1470770
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 3614239
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 8188
        }
      ],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "current_worktree_shadow_logs",
      "manifest_control_candidate_count": 25,
      "market_data_like_count": 9,
      "max_depth": 2,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs",
      "raw_market_blob_count": 5,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 254625
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\canary_restart_governance_status.jsonl",
          "size_bytes": 8453
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "size_bytes": 8375704
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_registry_audit.jsonl",
          "size_bytes": 478526
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_ledger.jsonl",
          "size_bytes": 741802
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_budget_ledger.jsonl",
          "size_bytes": 4581
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\es_mes_preregistration_status.jsonl",
          "size_bytes": 86848
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\exit_management_shadow_status.jsonl",
          "size_bytes": 1441477
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\external_source_blocker_status.jsonl",
          "size_bytes": 1167576
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
          "size_bytes": 50673
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\lto_blocked_lane_status.jsonl",
          "size_bytes": 2375
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\ml_shadow_status.jsonl",
          "size_bytes": 207367
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
          "size_bytes": 230299
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\notification_queue_dead_zone_status.jsonl",
          "size_bytes": 40278
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\orderflow_primitives_status.jsonl",
          "size_bytes": 1092750
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\proxy_blocker_status.jsonl",
          "size_bytes": 189364
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\session_volatility_sweep_status.jsonl",
          "size_bytes": 45777
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_hardening_status.jsonl",
          "size_bytes": 1470770
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\shadow_observer_status.jsonl",
          "size_bytes": 3614239
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl",
          "size_bytes": 8188
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
          "size_bytes": 28854
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\broker_actual_r_audit.jsonl",
          "size_bytes": 384793
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_features_log.jsonl",
          "size_bytes": 10934530
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_ltf_path_order.jsonl",
          "size_bytes": 14045800
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_mso_snapshot_joins.jsonl",
          "size_bytes": 250212
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\candidate_path_follow.jsonl",
          "size_bytes": 23937425
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\context_control_audit.jsonl",
          "size_bytes": 18249472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\continuation_no_retrace_candidates.jsonl",
          "size_bytes": 162403
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\continuation_no_retrace_resolutions.jsonl",
          "size_bytes": 481204
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\cusum_candidate_rate_daily.csv",
          "size_bytes": 1880
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\d1_bias_lag.jsonl",
          "size_bytes": 115078
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\d1_bias_lag_recovery.jsonl",
          "size_bytes": 9355
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\daily_pnl.json",
          "size_bytes": 1321
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\daily_pnl.json.bak",
          "size_bytes": 231
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\daily_pnl_history.jsonl",
          "size_bytes": 1537
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_confluence.jsonl",
          "size_bytes": 12682
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\databento_live_trigger_decisions.jsonl",
          "size_bytes": 360665
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\decision_layer_diagnostics_join.jsonl",
          "size_bytes": 1335387
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\direction_emission_xau_audit.jsonl",
          "size_bytes": 107922
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\displacement_events.jsonl",
          "size_bytes": 64211
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
          "size_bytes": 816
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
          "size_bytes": 4594
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
          "size_bytes": 2688
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
          "size_bytes": 3939
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
          "size_bytes": 605
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 974449190,
      "truncated": false
    },
    {
      "dir_count": 4,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".csv": 56,
        ".json": 28,
        ".md": 3,
        ".txt": 1,
        "[no_ext]": 2
      },
      "file_count": 90,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "current_worktree_exports",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 56,
      "max_depth": 4,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\.DS_Store",
          "size_bytes": 6148
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\ftmo_spread_check.json",
          "size_bytes": 4076
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\reasoning_text_mining_findings.json",
          "size_bytes": 701
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\candle_export_summary.json",
          "size_bytes": 2935
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\GBPUSD_D1.csv",
          "size_bytes": 34654
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\GBPUSD_H1.csv",
          "size_bytes": 938675
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\GBPUSD_H4.csv",
          "size_bytes": 236906
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\GBPUSD_M15.csv",
          "size_bytes": 3714551
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\candle_redownload\\XAUUSD_D1.csv",
          "size_bytes": 32212
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\economic_calendar_summary.json",
          "size_bytes": 478
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\GBPUSD_M1_recent.csv",
          "size_bytes": 7636290
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\hourly_volatility_profile.json",
          "size_bytes": 41134
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\m1_data_summary.json",
          "size_bytes": 1714
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\tick_data_availability.json",
          "size_bytes": 3821
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\trade_entry_spreads.json",
          "size_bytes": 128
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\mt5_data_dump\\XAUUSD_M1_recent.csv",
          "size_bytes": 7245921
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\multi_instrument\\.DS_Store",
          "size_bytes": 6148
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\multi_instrument\\align_injection_design.md",
          "size_bytes": 1280
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\multi_instrument\\AUDUSD_D1.csv",
          "size_bytes": 166870
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\exports\\multi_instrument\\AUDUSD_H1.csv",
          "size_bytes": 1229727
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 93667713,
      "truncated": false
    },
    {
      "dir_count": 2147,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bak": 5,
        ".bat": 4,
        ".csv": 713,
        ".depth": 2,
        ".err": 1,
        ".html": 68,
        ".jpeg": 42,
        ".jpg": 8,
        ".json": 5747,
        ".jsonl": 1092,
        ".jsonl.gz": 13,
        ".local": 1,
        ".lock": 164,
        ".log": 238,
        ".md": 1945,
        ".mq5": 1,
        ".out": 1,
        ".parquet": 109,
        ".patch": 1,
        ".pdf": 5,
        ".pkl": 7,
        ".png": 114,
        ".ps1": 3,
        ".py": 1166,
        ".pyc": 85,
        ".scid": 4,
        ".sh": 11,
        ".template": 2,
        ".tmp": 2,
        ".toml": 1,
        ".txt": 144,
        ".utcdate": 9,
        ".vbs": 2,
        ".xlsx": 2,
        ".yaml": 890,
        "[no_ext]": 30
      },
      "file_count": 12632,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_fpb_source_audit_final\\test_parse_scid_independent_re0\\TEST.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_fpb_source_audit_final\\test_parse_scid_independent_re0\\TEST.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_hard_floor_requires_previ0\\6BM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_hard_floor_requires_previ0\\6BM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_raw_byte_rehash_uses_mani0\\NQM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_raw_byte_rehash_uses_mani0\\NQM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_selected_hash_overlap_blo0\\YMM26-CBOT.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_selected_hash_overlap_blo0\\YMM26-CBOT.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_0\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 567
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_1\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_1\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 567
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_2\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_2\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 567
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_canary_restart_governance1\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_canary_restart_governance1\\shadow_logs\\canary_restart_governance_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1620
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_path_contract_a0\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_path_contract_a0\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1743
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra0\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra0\\shadow_logs\\candidate_registry_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 2244
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra2\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra2\\shadow_logs\\candidate_registry_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 2250
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1241
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 6741
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1217
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1094
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1554
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "sha256": "63b2fadaf818bf4dc1b604ec6efce12dd139dd1087b280898de35190f4d48542",
          "size_bytes": 15549
        }
      ],
      "is_dir": true,
      "label": "absolute_main_repo",
      "manifest_control_candidate_count": 539,
      "market_data_like_count": 843,
      "max_depth": 3,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 168,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent",
      "raw_market_blob_count": 130,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "size_bytes": 15549
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 567
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_1\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 567
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_broker_actual_r_contract_2\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 567
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_canary_restart_governance1\\shadow_logs\\canary_restart_governance_status.jsonl",
          "size_bytes": 1620
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_path_contract_a0\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "size_bytes": 1743
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra0\\shadow_logs\\candidate_registry_audit.jsonl",
          "size_bytes": 2244
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_candidate_registry_contra2\\shadow_logs\\candidate_registry_audit.jsonl",
          "size_bytes": 2250
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 1241
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl",
          "size_bytes": 6741
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\external_source_blocker_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl",
          "size_bytes": 1217
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\ml_shadow_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl",
          "size_bytes": 1094
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\proxy_blocker_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl",
          "size_bytes": 1554
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_tmp\\test_close_gaps_can_refresh_si0\\shadow_logs\\sierra_confluence_source_status.jsonl.lock",
          "size_bytes": 0
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.DS_Store",
          "size_bytes": 24580
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.env",
          "size_bytes": 491
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.env.local",
          "size_bytes": 420
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.gitattributes",
          "size_bytes": 939
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.gitignore",
          "size_bytes": 8494
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\AGENTS.md",
          "size_bytes": 36948
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\asba.txt",
          "size_bytes": 354
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\autocorrelation_baselines.md",
          "size_bytes": 2055
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\batch_backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CEO_DIRECTIVE_COMPLETION_REPORT.md",
          "size_bytes": 1662
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CLAUDE.md",
          "size_bytes": 33549
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CORRECTED_INTELLIGENCE_BRIEF_APRIL7.md",
          "size_bytes": 5032
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\DATA_VERIFICATION_MATRIX.md",
          "size_bytes": 11668
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\decomposition_raw_results.json",
          "size_bytes": 9167
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\decomposition_real_mso_test.md",
          "size_bytes": 6466
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\defaults_and_tests_audit.md",
          "size_bytes": 11784
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\demo_infrastructure.py",
          "size_bytes": 6144
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\devils_advocate_test_results.md",
          "size_bytes": 4677
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\DIVERGENCE_SAMPLER_REPORT.md",
          "size_bytes": 8642
        }
      ],
      "sample_parser_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\knowledge_base_backtest\\analysis\\trade_capture_pressure_test_runner.py",
          "size_bytes": 43435
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\podcast_pipeline\\test_results\\audit_h34_calendar.py",
          "size_bytes": 2935
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\podcast_pipeline\\verification\\verify_batch_b.py",
          "size_bytes": 16326
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\a4_trending_bull_replay_2026-04-28\\build_realized_r_join.py",
          "size_bytes": 6653
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\academic_pipeline\\scripts\\q_1_1_mi_audit.py",
          "size_bytes": 32220
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\directional_concentration_audit_2026-04-24\\scripts\\structure_stickiness.py",
          "size_bytes": 5218
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\halluc_4_cross_instrument_context\\build_audit.py",
          "size_bytes": 15887
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\halluc_4_cross_instrument_context\\build_combined_audit.py",
          "size_bytes": 4954
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\lira_ab_deep_forensic\\red_team\\red_team_verify.py",
          "size_bytes": 27334
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\ml_program\\audit\\_audit_run.py",
          "size_bytes": 19477
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\ml_program\\scout\\build_scout_matrix.py",
          "size_bytes": 26687
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\ml_program\\scripts\\build_catalog_v2.py",
          "size_bytes": 5607
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\ml_program\\scripts\\_build_regime_catalog.py",
          "size_bytes": 12338
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\phase1_xauusd_reverse_engineering\\build_master_df.py",
          "size_bytes": 8648
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\phase1_xauusd_reverse_engineering\\_build_dataset.py",
          "size_bytes": 5758
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\build_otg0_control_artifacts_2026_05_07.py",
          "size_bytes": 53687
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\sierrachart_data_source_research_2026-05-02\\tools\\sierra_depth_probe.py",
          "size_bytes": 12168
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\scratch\\intra_c\\step3_verify_crosstab.py",
          "size_bytes": 4328
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\scripts\\audit_canary_restart_governance.py",
          "size_bytes": 7586
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\scripts\\audit_databento_live_trigger_policy.py",
          "size_bytes": 6655
        }
      ],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_fpb_source_audit_final\\test_parse_scid_independent_re0\\TEST.scid",
          "size_bytes": 136
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_hard_floor_requires_previ0\\6BM26-CME.scid",
          "size_bytes": 176
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_raw_byte_rehash_uses_mani0\\NQM26-CME.scid",
          "size_bytes": 216
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_g12_reaudit_debug\\test_selected_hash_overlap_blo0\\YMM26-CBOT.scid",
          "size_bytes": 96
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "size_bytes": 3882626
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "size_bytes": 4176378
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "size_bytes": 6350848
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "size_bytes": 4354929
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "size_bytes": 145311
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "size_bytes": 4856218
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "size_bytes": 3892480
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "size_bytes": 5377035
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "size_bytes": 4477088
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "size_bytes": 3683255
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "size_bytes": 174574
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "size_bytes": 3494289
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "size_bytes": 4379561
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "size_bytes": 350286
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 4589345190,
      "truncated": false
    },
    {
      "dir_count": 95,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".csv": 451,
        ".json": 342,
        ".jsonl": 165,
        ".log": 6,
        ".md": 2,
        ".parquet": 100,
        ".txt": 2,
        ".xlsx": 6,
        ".zst": 113
      },
      "file_count": 1187,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\codex_probe_eurusd_20260415\\manifest.json",
          "sha256": "e6111e723abde9bd997ac408d63b1515f2479d832a69ca5464391312e34f5ad7",
          "size_bytes": 1858
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_candidate_gap_20260501\\manifest.json",
          "sha256": "648fe634b4d9bdfdc334e1bd28b8dad9f088700fcd14db6066464c4cac238a9e",
          "size_bytes": 3267
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m15_2022_2026_fn_chunked_v1\\manifest.json",
          "sha256": "910ad094abff1dffe1c994aef3512f8e2f0be32debb131b40c01777c58a9c301",
          "size_bytes": 5457
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\manifest.json",
          "sha256": "e1fed7352439b8a8e240ffeaf42c6f2601c2ef5d79c092fd4ef8198b807807ed",
          "size_bytes": 18542
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\manifest.json",
          "sha256": "39467b736e1056e93e850bfdd93ada3f32aec112c4e423338aea34801bd1b9e4",
          "size_bytes": 10191
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_20220501\\manifest.json",
          "sha256": "b3b2b516a547051b2012b91ab62b2d2649fed0f025e254d5a9e1eda786266ba0",
          "size_bytes": 1971
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_after_maxbars\\manifest.json",
          "sha256": "06fb2e21244c39b56682e8b6e89b6b36714f9f301545e8714490c57164c23b3a",
          "size_bytes": 1993
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\manifest.json",
          "sha256": "a4cec6442c7608635159dddd0d98abe5cd7ca659b68d31271c6db87ed4a33763",
          "size_bytes": 27120
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\manifest.json",
          "sha256": "d1979df60412ce6c01426e6546ec335dcaf7d4fed55784bc6129786fb4cae9a5",
          "size_bytes": 22191
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
          "size_bytes": 5253
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
          "size_bytes": 5248
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
          "size_bytes": 89398
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
          "size_bytes": 5263
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
          "size_bytes": 5268
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
          "size_bytes": 5292
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
          "size_bytes": 5330
        }
      ],
      "is_dir": true,
      "label": "absolute_main_repo_data",
      "manifest_control_candidate_count": 16,
      "market_data_like_count": 557,
      "max_depth": 7,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
      "raw_market_blob_count": 106,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\codex_probe_eurusd_20260415\\manifest.json",
          "size_bytes": 1858
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_candidate_gap_20260501\\manifest.json",
          "size_bytes": 3267
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m15_2022_2026_fn_chunked_v1\\manifest.json",
          "size_bytes": 5457
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\manifest.json",
          "size_bytes": 18542
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\manifest.json",
          "size_bytes": 10191
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_20220501\\manifest.json",
          "size_bytes": 1971
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_after_maxbars\\manifest.json",
          "size_bytes": 1993
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\manifest.json",
          "size_bytes": 27120
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\manifest.json",
          "size_bytes": 22191
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "size_bytes": 5253
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "size_bytes": 5248
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "size_bytes": 89398
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "size_bytes": 5263
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "size_bytes": 5268
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "size_bytes": 5292
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "size_bytes": 5330
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\DXY_D1.csv",
          "size_bytes": 20017
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\economic_calendar.csv",
          "size_bytes": 1572
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_D1.csv",
          "size_bytes": 30108
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_H1.csv",
          "size_bytes": 828266
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_H4.csv",
          "size_bytes": 209541
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_M15.csv",
          "size_bytes": 3273362
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_M5.csv",
          "size_bytes": 5291443
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_D1.csv",
          "size_bytes": 177741
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_H1.csv",
          "size_bytes": 1165502
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_H4.csv",
          "size_bytes": 580221
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_M15.csv",
          "size_bytes": 2902096
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_M5.csv",
          "size_bytes": 19603
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_D1.csv",
          "size_bytes": 28780
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_H1.csv",
          "size_bytes": 744327
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_H4.csv",
          "size_bytes": 197086
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M15.csv",
          "size_bytes": 2934918
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M5.csv",
          "size_bytes": 5301737
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\news_calendar.json",
          "size_bytes": 3972
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_D1.csv",
          "size_bytes": 26899
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_H1.csv",
          "size_bytes": 723400
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "size_bytes": 3882626
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "size_bytes": 4176378
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "size_bytes": 6350848
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "size_bytes": 4354929
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "size_bytes": 145311
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "size_bytes": 4856218
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "size_bytes": 3892480
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "size_bytes": 5377035
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "size_bytes": 4477088
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "size_bytes": 3683255
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "size_bytes": 174574
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "size_bytes": 3494289
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "size_bytes": 4379561
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "size_bytes": 350286
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 22655017307,
      "truncated": false
    },
    {
      "dir_count": 7,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".json": 7,
        ".md": 1,
        ".parquet": 100
      },
      "file_count": 108,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        }
      ],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "absolute_main_repo_data_ticks",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 100,
      "max_depth": 4,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "raw_market_blob_count": 100,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\README.md",
          "size_bytes": 5376
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\.state.json",
          "size_bytes": 175
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\.state.json",
          "size_bytes": 176
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\.state.json",
          "size_bytes": 178
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\.state.json",
          "size_bytes": 189
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\.state.json",
          "size_bytes": 177
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\.state.json",
          "size_bytes": 174
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\.state.json",
          "size_bytes": 176
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
          "size_bytes": 3882626
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
          "size_bytes": 4176378
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
          "size_bytes": 6350848
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
          "size_bytes": 4354929
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
          "size_bytes": 145311
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
          "size_bytes": 4856218
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
          "size_bytes": 3892480
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
          "size_bytes": 5377035
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
          "size_bytes": 4477088
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
          "size_bytes": 3683255
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-10.parquet",
          "size_bytes": 174574
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-11.parquet",
          "size_bytes": 3494289
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-12.parquet",
          "size_bytes": 4379561
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-13.parquet",
          "size_bytes": 350286
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet",
          "size_bytes": 2638946
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet",
          "size_bytes": 2811846
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet",
          "size_bytes": 3926086
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet",
          "size_bytes": 2680981
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet",
          "size_bytes": 70932
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
          "size_bytes": 3059442
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 468415565,
      "truncated": false
    },
    {
      "dir_count": 58,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".json": 294,
        ".jsonl": 161,
        ".log": 6,
        ".txt": 2,
        ".xlsx": 6,
        ".zst": 113
      },
      "file_count": 582,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        }
      ],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "absolute_main_repo_data_external",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 6,
      "max_depth": 6,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
      "raw_market_blob_count": 6,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
          "size_bytes": 389258024
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
          "size_bytes": 54524286
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
          "size_bytes": 1549414
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
          "size_bytes": 389258092
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
          "size_bytes": 11658816
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
          "size_bytes": 54539857
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
          "size_bytes": 54539857
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
          "size_bytes": 54539857
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
          "size_bytes": 54539857
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
          "size_bytes": 1557200
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
          "size_bytes": 117120
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
          "size_bytes": 283585832
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
          "size_bytes": 11052288
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
          "size_bytes": 51702752
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
          "size_bytes": 51702752
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
          "size_bytes": 51702752
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
          "size_bytes": 51702752
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
          "size_bytes": 1485988
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\smoke_phase3_m15_20260430T235137Z.jsonl",
          "size_bytes": 117120
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
          "size_bytes": 283600326
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T224531Z.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\ETF_Flows_March_2026_20260430T234945Z.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225355Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225417Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T225431Z.xlsx",
          "size_bytes": 249270
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\wgc\\GDT_Tables_Q126_EN_20260430T234945Z.xlsx",
          "size_bytes": 249270
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 21024659579,
      "truncated": false
    },
    {
      "dir_count": 1,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bak": 2,
        ".csv": 4,
        ".json": 22,
        ".jsonl": 100,
        ".jsonl.gz": 13,
        ".lock": 39,
        ".log": 1,
        ".tmp": 1
      },
      "file_count": 182,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-04.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-04.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-05.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-05.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-06.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-06.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-07.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-07.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-09.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-09.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-10.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-10.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-11.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-11.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-12.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-12.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 255834
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 8453
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 8404652
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 480776
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 744781
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 4581
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 86843
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1443533
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 1200729
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 53064
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 2372
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 213360
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl.lock read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl.lock",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 0
        },
        {
          "exact_rehash_procedure": "Hash C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 235918
        }
      ],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "absolute_main_repo_shadow_logs",
      "manifest_control_candidate_count": 39,
      "market_data_like_count": 17,
      "max_depth": 2,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
      "raw_market_blob_count": 13,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl",
          "size_bytes": 255834
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl",
          "size_bytes": 8453
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl",
          "size_bytes": 8404652
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
          "size_bytes": 480776
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl",
          "size_bytes": 744781
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl",
          "size_bytes": 4581
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl",
          "size_bytes": 86843
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl",
          "size_bytes": 1443533
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl",
          "size_bytes": 1200729
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
          "size_bytes": 53064
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl",
          "size_bytes": 2372
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl",
          "size_bytes": 213360
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
          "size_bytes": 235918
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.d1_bias_lag_state.15480.tmp",
          "size_bytes": 519
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.d1_bias_lag_state.json",
          "size_bytes": 517
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.displacement_state.json",
          "size_bytes": 163
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.GBPJPY.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.GBPUSD.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.json",
          "size_bytes": 1364
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.NAS100.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.US30_cash.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.USDJPY.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.XAGUSD.json",
          "size_bytes": 74
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.XAUUSD.json",
          "size_bytes": 84
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
          "size_bytes": 28854
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\broker_actual_r_audit.jsonl",
          "size_bytes": 386560
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_features_log.jsonl",
          "size_bytes": 11013678
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_ltf_path_order.jsonl",
          "size_bytes": 14147239
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_ltf_path_order.jsonl.lock",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_mso_snapshot_joins.jsonl",
          "size_bytes": 250212
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_follow.jsonl",
          "size_bytes": 24032086
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_audit.jsonl",
          "size_bytes": 18312543
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\continuation_no_retrace_candidates.jsonl",
          "size_bytes": 162403
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies_2026-05-06.jsonl.gz",
          "size_bytes": 816
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-29.jsonl.gz",
          "size_bytes": 4594
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-04-30.jsonl.gz",
          "size_bytes": 2688
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-01.jsonl.gz",
          "size_bytes": 3939
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-03.jsonl.gz",
          "size_bytes": 605
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-04.jsonl.gz",
          "size_bytes": 6620
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-05.jsonl.gz",
          "size_bytes": 14158
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-06.jsonl.gz",
          "size_bytes": 4554
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-07.jsonl.gz",
          "size_bytes": 4724
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-09.jsonl.gz",
          "size_bytes": 5841
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-10.jsonl.gz",
          "size_bytes": 547
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-11.jsonl.gz",
          "size_bytes": 2950
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences_2026-05-12.jsonl.gz",
          "size_bytes": 3389
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 989254300,
      "truncated": false
    },
    {
      "dir_count": 4,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".csv": 56,
        ".json": 28,
        ".md": 3,
        ".txt": 1,
        "[no_ext]": 2
      },
      "file_count": 90,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "absolute_main_repo_exports",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 56,
      "max_depth": 4,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\.DS_Store",
          "size_bytes": 6148
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\ftmo_spread_check.json",
          "size_bytes": 4076
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\reasoning_text_mining_findings.json",
          "size_bytes": 701
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\candle_export_summary.json",
          "size_bytes": 2935
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_D1.csv",
          "size_bytes": 34654
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_H1.csv",
          "size_bytes": 938675
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_H4.csv",
          "size_bytes": 236906
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_M15.csv",
          "size_bytes": 3714551
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\XAUUSD_D1.csv",
          "size_bytes": 32212
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\economic_calendar_summary.json",
          "size_bytes": 478
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\GBPUSD_M1_recent.csv",
          "size_bytes": 7636290
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\hourly_volatility_profile.json",
          "size_bytes": 41134
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\m1_data_summary.json",
          "size_bytes": 1714
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\tick_data_availability.json",
          "size_bytes": 3821
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\trade_entry_spreads.json",
          "size_bytes": 128
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\XAUUSD_M1_recent.csv",
          "size_bytes": 7245921
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\.DS_Store",
          "size_bytes": 6148
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\align_injection_design.md",
          "size_bytes": 1280
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\AUDUSD_D1.csv",
          "size_bytes": 166870
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\AUDUSD_H1.csv",
          "size_bytes": 1229727
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 93667713,
      "truncated": false
    },
    {
      "dir_count": 43,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bat": 6,
        ".csv": 14,
        ".json": 48,
        ".jsonl": 7,
        ".log": 65,
        ".md": 368,
        ".patch": 1,
        ".png": 30,
        ".ps1": 1,
        ".py": 78,
        ".pyc": 3,
        ".sh": 18,
        ".toml": 6,
        ".txt": 15,
        "[no_ext]": 24
      },
      "file_count": 684,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\lto002_debug\\shadow_logs\\candidate_registry_audit.jsonl read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\lto002_debug\\shadow_logs\\candidate_registry_audit.jsonl",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 2196
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_recovery\\live_mechanical_lfs_repair_manifest_20260511T034433Z.json",
          "sha256": "98b612f7a61872ce83cf590564c456793bfd83abef3f06f819f9a616883972ed",
          "size_bytes": 874
        }
      ],
      "is_dir": true,
      "label": "tmp_prior_worktrees_parent",
      "manifest_control_candidate_count": 14,
      "market_data_like_count": 14,
      "max_depth": 2,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_recovery\\live_mechanical_lfs_repair_manifest_20260511T034433Z.json",
          "size_bytes": 874
        },
        {
          "path": "C:\\tmp\\lto002_debug\\shadow_logs\\candidate_registry_audit.jsonl",
          "size_bytes": 2196
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\all_fills.csv",
          "size_bytes": 22782
        },
        {
          "path": "C:\\tmp\\cascade_full_template.txt",
          "size_bytes": 25543
        },
        {
          "path": "C:\\tmp\\debug_wilcoxon.log",
          "size_bytes": 680
        },
        {
          "path": "C:\\tmp\\debug_wilcoxon2.log",
          "size_bytes": 551
        },
        {
          "path": "C:\\tmp\\g0_fpb_sealed_0.pyc",
          "size_bytes": 61007
        },
        {
          "path": "C:\\tmp\\g0_fpb_sealed_1.pyc",
          "size_bytes": 16540
        },
        {
          "path": "C:\\tmp\\g0_fpb_sealed_2.pyc",
          "size_bytes": 6218
        },
        {
          "path": "C:\\tmp\\gtosg_admin_cleanup.log",
          "size_bytes": 7979135
        },
        {
          "path": "C:\\tmp\\gtos_admin_cleanup_log.txt",
          "size_bytes": 241
        },
        {
          "path": "C:\\tmp\\GTOS_Tokyo_KZ_Wake_Launch.ps1",
          "size_bytes": 820
        },
        {
          "path": "C:\\tmp\\h2_only.patch",
          "size_bytes": 642
        },
        {
          "path": "C:\\tmp\\j46_j49_agg2.log",
          "size_bytes": 3458
        },
        {
          "path": "C:\\tmp\\j46_j49_agg3.log",
          "size_bytes": 1731
        },
        {
          "path": "C:\\tmp\\LIVE_STATE_before_otr061_merge_20260507_173102.md",
          "size_bytes": 17131
        },
        {
          "path": "C:\\tmp\\noapi_mech_replay_paths.txt",
          "size_bytes": 6514
        },
        {
          "path": "C:\\tmp\\null_test.json",
          "size_bytes": 5382
        },
        {
          "path": "C:\\tmp\\a2_test\\report.md",
          "size_bytes": 4211
        },
        {
          "path": "C:\\tmp\\a2_test\\series.jsonl",
          "size_bytes": 406
        },
        {
          "path": "C:\\tmp\\a2_test\\summary.json",
          "size_bytes": 3106
        },
        {
          "path": "C:\\tmp\\dumb_baseline_sanity\\.state.json",
          "size_bytes": 110
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 564550445,
      "truncated": false
    },
    {
      "dir_count": 4296,
      "errors": [
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\ANTI_BOXING_ADV002\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED15_POI_BOUNDS\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED15_POI_BOUNDS\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_LTF_ATTACH\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_LTF_ATTACH\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_MAIN_RECONCILIATION_APPROVAL_REQUIREMENT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_MAIN_RECONCILIATION_APPROVAL_REQUIREMENT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_MAIN_RECONCILIATION_APPROVAL_REQUIREMENT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_MAIN_RECONCILIATION_APPROVAL_REQUIREMENT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\build_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\\\build_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\verify_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\\\verify_g0_nofill_historical_partition_source_binding_synthesis_control_review_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_BASELINE_CONTROL_ROLE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_BASELINE_CONTROL_ROLE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_BASELINE_CONTROL_ROLE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_BASELINE_CONTROL_ROLE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_GIT_LFS_DIRTY_NOLEAK_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_GIT_LFS_DIRTY_NOLEAK_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_GIT_LFS_DIRTY_NOLEAK_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_GIT_LFS_DIRTY_NOLEAK_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g0_scid_forward_capture_additive_synthesis_control\\SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_scid_forward_capture_additive_synthesis_control\\\\SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_CATALOG_ROW_COUNT_SCHEMA_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_CATALOG_ROW_COUNT_SCHEMA_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_HASH_LARGE_FILE_DEFERRAL_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_HASH_LARGE_FILE_DEFERRAL_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_INTEGRATION_GUIDE_USABILITY_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_INTEGRATION_GUIDE_USABILITY_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_INTEGRATION_GUIDE_USABILITY_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_INTEGRATION_GUIDE_USABILITY_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ROOT_RESOLVER_CONFIG_SCHEMA_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit\\G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT_GOAL_PROMPT_2026-05-09.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit\\\\G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT_GOAL_PROMPT_2026-05-09.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\verify_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\verify_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_OWNER_GATE_DEPENDENCY_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_OWNER_GATE_DEPENDENCY_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\\\build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\verify_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\\\verify_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\\\G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\\\\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_asof_quarantined_neutral_target_execution_packet_audit\\G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_asof_quarantined_neutral_target_execution_packet_audit\\\\G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_asof_quarantined_neutral_target_execution_packet_audit\\G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_asof_quarantined_neutral_target_execution_packet_audit\\\\G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_MANIFEST_BINDING_AUDIT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_MANIFEST_BINDING_AUDIT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SCOPED_DIRTY_STATE_AUDIT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SCOPED_DIRTY_STATE_AUDIT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SCOPED_DIRTY_STATE_AUDIT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SCOPED_DIRTY_STATE_AUDIT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_VERIFIER_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_VERIFIER_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_VERIFIER_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_VERIFIER_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_combined_source_search_and_forward_capture_route_audit\\G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_combined_source_search_and_forward_capture_route_audit\\\\G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_combined_source_search_and_forward_capture_route_audit\\G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_combined_source_search_and_forward_capture_route_audit\\\\G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit\\build_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit\\\\build_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit\\verify_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit\\\\verify_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\NOFILL_HISTORICAL_SEALED_VALIDATION_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_sealed_validation_partition_and_source_binding\\\\NOFILL_HISTORICAL_SEALED_VALIDATION_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\NOFILL_HISTORICAL_SEALED_VALIDATION_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_sealed_validation_partition_and_source_binding\\\\NOFILL_HISTORICAL_SEALED_VALIDATION_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\\\build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_source_state_capture_gap_closure_and_tick_export_manifest_route\\\\verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_OWNER_APPROVAL_RESTART_ROLLBACK_GATE_DOSSIER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_OWNER_APPROVAL_RESTART_ROLLBACK_GATE_DOSSIER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\build_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\\\build_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\\\test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis\\\\verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\\\build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\\\test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py'",
        "C:\\tmp\\gtos_nextwave\\BLOCKED17_ORDERFLOW_PROXY\\research\\science_program_2026_05\\06_outcome_testing\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\BLOCKED17_ORDERFLOW_PROXY\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint\\\\verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\EXP_R1_LINEAGE\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_forward_source_capture_implementation_synthesis_readiness_route\\\\verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\build_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CORE_FAMILY_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_CROSS_FAMILY_SYNTHESIS_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_DISCOVERY_PATH_LABEL_SYNTHESIS_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_EXCLUDED_HIGH_VALUE_FAMILY_ROUTE_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_COVERAGE_DENOMINATOR_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_LIQUIDITY_ADJACENT_ROUTE_RANKING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_REPLAY_SUBSTRATE_SYNTHESIS_REPORT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\test_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection\\\\verify_g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection_2026_05_10.py'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_ACQUISITION_MANIFEST_CLASSIFICATION_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_REPAIR_FOLLOWUP_SOURCE_REQUEST_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_gtos_local_research_data_catalog_source_control_audit\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_gtos_local_research_data_catalog_source_control_audit\\\\G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_SEARCH_RESULT_MISSING_WINDOW_ROUTING_AUDIT_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_additive_logger_implementation_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_forward_source_capture_implementation_design_audit\\\\G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_scid_capture_schema_to_runtime_test_harness_synthetic_only_audit\\\\G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT_SELF_VERIFICATION_AND_TEST_RESULT_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_implementation_design_package_from_offline_schema_synthesis\\\\SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_forward_capture_readonly_monitoring_alignment_expansion\\\\SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.md'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json'",
        "C:\\tmp\\gtos_nextwave\\READY8_RESULT_PACKET\\research\\science_program_2026_05\\06_outcome_testing\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json: FileNotFoundError: [WinError 3] The system cannot find the path specified: 'C:\\\\tmp\\\\gtos_nextwave\\\\READY8_RESULT_PACKET\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis\\\\SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json'"
      ],
      "exists": true,
      "extension_counts": {
        ".bak": 18,
        ".bat": 12,
        ".csv": 3654,
        ".depth": 12,
        ".html": 552,
        ".jpeg": 252,
        ".jpg": 12,
        ".js": 6,
        ".json": 40517,
        ".jsonl": 2330,
        ".jsonl.gz": 48,
        ".lgb": 84,
        ".log": 930,
        ".md": 23473,
        ".mq5": 6,
        ".parquet": 90,
        ".patch": 6,
        ".pdf": 30,
        ".png": 768,
        ".ps1": 18,
        ".py": 10180,
        ".sh": 66,
        ".template": 12,
        ".toml": 6,
        ".txt": 1248,
        ".vbs": 12,
        ".xml": 18,
        ".yaml": 2502,
        "[no_ext]": 210
      },
      "file_count": 87072,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".gz"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\feature_matrix.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\feature_matrix.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".parquet"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".depth"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-02_delayed.depth read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-02_delayed.depth",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".depth"
        },
        {
          "exact_rehash_procedure": "Hash C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv read-only in a source-control lane if it becomes a consumed source.",
          "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
          "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
          "size_bytes": 3047
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "sha256": "ca93cc0d58542234f84ab20adcd4997b90ed0fa6f6cbb0521ea9da08cb8525d3",
          "size_bytes": 15709
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\config\\shadow_observer_registry.yaml",
          "sha256": "1b8000c5283edd48f7f68d7d1b521d76a080f6f531d92cced9527f3b898733c0",
          "size_bytes": 5793
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "sha256": "bb5d4e1b8785abc503d95c106277ee82675f7751a3a72910c34a06061432c150",
          "size_bytes": 5253
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "sha256": "3a86f262ce4c876cee8a5283b63517045009d2bc72a9f6868b0598d9f14cc565",
          "size_bytes": 5248
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "sha256": "62da878d2e54d4131f90b98e9b1baa49aa087f2e69c333668658189c037027e4",
          "size_bytes": 89398
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "sha256": "5f031d556e4485d1a00c43a69fa3854aca5d0c7c8ef5dfcf470512763a4af861",
          "size_bytes": 5263
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "sha256": "deb3a802dafb7c73f41ddfadd3811d0d535f99870fa89c564a28a03a4b05aea6",
          "size_bytes": 5268
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "sha256": "e1e2f972bfcb00e91918a0b9b69fb92b718480664cf79e890aec53bc3812ea19",
          "size_bytes": 5292
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "sha256": "16620c3e3e42c0c03f99940bb811a01e00dab44f7f6313fe96fce2914fedcec8",
          "size_bytes": 5330
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\operations\\data_manifest.md",
          "sha256": "0c6f557574b8b56e2010b69cc779d6485fcf0a7509e462e381537b61cec56f89",
          "size_bytes": 7657
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\cascade_prompt_status_2026-04-25.md",
          "sha256": "83b972d77aeef7d8fdcc37fdef2acb9709e73bd57f06e9549aab02873a26ebba",
          "size_bytes": 14843
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
          "sha256": "998fad54e7e0934a282106ec40b55dbdb152006c18a52dc36d63769306f1ade4",
          "size_bytes": 98303
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
          "sha256": "c2bb6094f91557e179c9d4fb21c88ec3f419313a430d1fc3af46fd14cbb1ba33",
          "size_bytes": 3375
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
          "sha256": "319b3bcf1f1ebeda390eb9ffad9f60f88e652dd671a58dd575da07e906ea3cd2",
          "size_bytes": 97675
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
          "sha256": "a9349666f9b6886f1558911a6d5651210762504459ecc3de54219b2cca324ce7",
          "size_bytes": 3269
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
          "sha256": "663b05a0581dda519a4e3254a2d1b3273e21d5f87a4a2c2aa3ccc01ccb8598a7",
          "size_bytes": 275351
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
          "sha256": "40efc5d4f7b4cf0dfa6d82a372c1e10aad69a381be062fa6908ef6024b134616",
          "size_bytes": 4616
        }
      ],
      "is_dir": true,
      "label": "tmp_gtos_nextwave_worktrees",
      "manifest_control_candidate_count": 11924,
      "market_data_like_count": 3804,
      "max_depth": 5,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 3676,
      "path": "C:\\tmp\\gtos_nextwave",
      "raw_market_blob_count": 150,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.context\\05_operations\\LIVE_MONITORING_LEDGER_2026-05-04.md",
          "size_bytes": 15709
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\config\\shadow_observer_registry.yaml",
          "size_bytes": 5793
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6b_to_gbpusd_pilot_20260504\\manifest.json",
          "size_bytes": 5253
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_6j_to_usdjpy_pilot_20260504\\manifest.json",
          "size_bytes": 5248
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_first_wave_bounded_conversion_20260504\\manifest.json",
          "size_bytes": 89398
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\manifest.json",
          "size_bytes": 5263
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_si_to_xagusd_pilot_20260504\\manifest.json",
          "size_bytes": 5268
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\manifest.json",
          "size_bytes": 5292
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\data\\sierra_ohlcv_roots\\sierra_ym_to_us30_cash_pilot_20260504\\manifest.json",
          "size_bytes": 5330
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\operations\\data_manifest.md",
          "size_bytes": 7657
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\cascade_prompt_status_2026-04-25.md",
          "size_bytes": 14843
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\a4_cohort_manifest.csv",
          "size_bytes": 3047
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.json",
          "size_bytes": 98303
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02.md",
          "size_bytes": 3375
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.json",
          "size_bytes": 97675
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md",
          "size_bytes": 3269
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json",
          "size_bytes": 275351
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\databento_orderflow_capture_2026-05-02\\ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md",
          "size_bytes": 4616
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.DS_Store",
          "size_bytes": 24580
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.git",
          "size_bytes": 82
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.gitattributes",
          "size_bytes": 939
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\.gitignore",
          "size_bytes": 8519
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\AGENTS.md",
          "size_bytes": 37009
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\asba.txt",
          "size_bytes": 354
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\autocorrelation_baselines.md",
          "size_bytes": 2055
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\batch_backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\CEO_DIRECTIVE_COMPLETION_REPORT.md",
          "size_bytes": 1662
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\CLAUDE.md",
          "size_bytes": 33556
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\CORRECTED_INTELLIGENCE_BRIEF_APRIL7.md",
          "size_bytes": 5032
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\DATA_VERIFICATION_MATRIX.md",
          "size_bytes": 11668
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\decomposition_raw_results.json",
          "size_bytes": 9167
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\decomposition_real_mso_test.md",
          "size_bytes": 6466
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\defaults_and_tests_audit.md",
          "size_bytes": 11942
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\demo_infrastructure.py",
          "size_bytes": 6144
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\devils_advocate_test_results.md",
          "size_bytes": 4677
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\DIVERGENCE_SAMPLER_REPORT.md",
          "size_bytes": 8642
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\dst_effect_analysis.md",
          "size_bytes": 2956
        }
      ],
      "sample_parser_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\knowledge_base_backtest\\analysis\\trade_capture_pressure_test_runner.py",
          "size_bytes": 43435
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\podcast_pipeline\\test_results\\audit_h34_calendar.py",
          "size_bytes": 2935
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\podcast_pipeline\\verification\\verify_batch_b.py",
          "size_bytes": 16326
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\a4_trending_bull_replay_2026-04-28\\build_realized_r_join.py",
          "size_bytes": 6653
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\academic_pipeline\\scripts\\q_1_1_mi_audit.py",
          "size_bytes": 32804
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase1\\_zeta_scratch\\04_visual_mso_audit.py",
          "size_bytes": 10111
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase1\\_zeta_scratch\\07_market_state_algo_verify.py",
          "size_bytes": 5573
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T1_scratch\\01_verify_gap_signature.py",
          "size_bytes": 4837
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\verify_xauusd_details.py",
          "size_bytes": 4711
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\directional_concentration_audit_2026-04-24\\scripts\\structure_stickiness.py",
          "size_bytes": 5344
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\halluc_4_cross_instrument_context\\build_audit.py",
          "size_bytes": 16309
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\halluc_4_cross_instrument_context\\build_combined_audit.py",
          "size_bytes": 5079
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\lira_ab_deep_forensic\\red_team\\red_team_verify.py",
          "size_bytes": 27334
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\audit\\_audit_run.py",
          "size_bytes": 19973
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\forensics\\2026-04-29\\_agent_k1_verify.py",
          "size_bytes": 32566
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\build_scout_matrix.py",
          "size_bytes": 27373
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scripts\\build_catalog_v2.py",
          "size_bytes": 5774
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scripts\\_build_regime_catalog.py",
          "size_bytes": 12467
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scripts\\features\\_build_liquidity_catalog.py",
          "size_bytes": 5942
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scripts\\features\\_build_structure_catalog.py",
          "size_bytes": 16126
        }
      ],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-26.jsonl.gz",
          "size_bytes": 670
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-27.jsonl.gz",
          "size_bytes": 2683
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\archive\\structure_detector_divergences\\2026-04\\structure_detector_divergences_2026-04-28.jsonl.gz",
          "size_bytes": 5326
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\both_semantics_events.parquet",
          "size_bytes": 742597
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\b_deep_audit_2026-04-19\\phase3\\_T3_scratch\\live_gate_sim.parquet",
          "size_bytes": 656740
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\phase_2\\position_mgmt\\_enriched_cohort.parquet",
          "size_bytes": 119899
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\ml_program\\scout\\feature_matrix.parquet",
          "size_bytes": 2739471
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_1\\features.parquet",
          "size_bytes": 274409
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_2\\features.parquet",
          "size_bytes": 338699
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_3\\features.parquet",
          "size_bytes": 337507
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_4\\features.parquet",
          "size_bytes": 338251
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_5\\features.parquet",
          "size_bytes": 306548
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_6\\features.parquet",
          "size_bytes": 302894
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_7\\features.parquet",
          "size_bytes": 306765
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\phase1_xauusd_reverse_engineering\\slice_8\\features.parquet",
          "size_bytes": 249227
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "size_bytes": 2209369
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "size_bytes": 2045401
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
          "size_bytes": 1584013
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-01_delayed.depth",
          "size_bytes": 160
        },
        {
          "path": "C:\\tmp\\gtos_nextwave\\ANTI_BOXING_ADV002\\research\\sierrachart_data_source_research_2026-05-02\\samples\\NQM26-CME.2026-05-02_delayed.depth",
          "size_bytes": 16792
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_WITH_ERRORS",
      "total_bytes": 24484552687,
      "truncated": false
    },
    {
      "dir_count": 0,
      "errors": [],
      "exists": true,
      "extension_counts": {},
      "file_count": 0,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "tmp_gtos_otb_prior_worktrees",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 0,
      "max_depth": 5,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_otb",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 0,
      "truncated": false
    },
    {
      "dir_count": 0,
      "errors": [],
      "exists": true,
      "extension_counts": {},
      "file_count": 0,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "tmp_gtos_otl_prior_worktrees",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 0,
      "max_depth": 5,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_otl",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 0,
      "truncated": false
    },
    {
      "dir_count": 0,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".jsonl": 2
      },
      "file_count": 2,
      "hash_deferral_records": [],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "tmp_large_file_backup_20260509",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 0,
      "max_depth": 5,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\tmp\\gtos_large_file_backup_20260509",
      "raw_market_blob_count": 0,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\tmp\\gtos_large_file_backup_20260509\\live_mechanical_strategy_shadow_outcomes.jsonl",
          "size_bytes": 192702816
        },
        {
          "path": "C:\\tmp\\gtos_large_file_backup_20260509\\ml_shadow_predictions.jsonl",
          "size_bytes": 112133099
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 304835915,
      "truncated": false
    },
    {
      "dir_count": 23,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bmp": 75,
        ".cht": 10,
        ".config": 30,
        ".cpp": 28,
        ".data": 12,
        ".defaultsettings": 1,
        ".depth": 165,
        ".dll": 3,
        ".dly": 2,
        ".exe": 6,
        ".h": 16,
        ".proto": 2,
        ".scid": 33,
        ".stdycollct": 3,
        ".twconfig": 3,
        ".txt": 3,
        ".wav": 25,
        ".xml": 14
      },
      "file_count": 431,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6AM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6AM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6BM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6CM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6CM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6EM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6JM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6JM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\6SM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\6SM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\AAPL.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\AAPL.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\AMZN-NQTV.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\AMZN-NQTV.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\CLM26-NYMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\CLM26-NYMEX.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\ESM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\ESM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\EURUSD.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\EURUSD.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\GCM26-COMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\M2KM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\M2KM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MCLM26-NYMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MCLM26-NYMEX.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MESM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MESM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MESU25-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MESU25-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MGCM26-COMEX.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MGCM26-COMEX.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MNQM26-CME.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MNQM26-CME.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\SierraChart\\Data\\MYMM26-CBOT.scid read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\SierraChart\\Data\\MYMM26-CBOT.scid",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".scid"
        }
      ],
      "hashed_control_samples": [],
      "is_dir": true,
      "label": "sierrachart_root",
      "manifest_control_candidate_count": 0,
      "market_data_like_count": 198,
      "max_depth": 5,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\SierraChart",
      "raw_market_blob_count": 198,
      "recursive": true,
      "sample_manifest_control_files": [],
      "sample_other_files": [
        {
          "path": "C:\\SierraChart\\Accounts4.config",
          "size_bytes": 35162
        },
        {
          "path": "C:\\SierraChart\\CrashReporter.exe",
          "size_bytes": 2554448
        },
        {
          "path": "C:\\SierraChart\\DataFilesFolder.txt",
          "size_bytes": 22
        },
        {
          "path": "C:\\SierraChart\\InternalOrderID2.data",
          "size_bytes": 16
        },
        {
          "path": "C:\\SierraChart\\KeyboardShortcuts4.config",
          "size_bytes": 1418
        },
        {
          "path": "C:\\SierraChart\\SC_remote_assistance.exe",
          "size_bytes": 23704120
        },
        {
          "path": "C:\\SierraChart\\Sierra4.config",
          "size_bytes": 631470
        },
        {
          "path": "C:\\SierraChart\\SierraChart.exe",
          "size_bytes": 2441216
        },
        {
          "path": "C:\\SierraChart\\SierraChartFileDownloader.exe",
          "size_bytes": 13503056
        },
        {
          "path": "C:\\SierraChart\\SierraChartStudies_64.dll",
          "size_bytes": 2152528
        },
        {
          "path": "C:\\SierraChart\\SierraChartStudies_ARM64.dll",
          "size_bytes": 2341968
        },
        {
          "path": "C:\\SierraChart\\SierraChart_64.exe",
          "size_bytes": 30089808
        },
        {
          "path": "C:\\SierraChart\\SierraChart_ARM64.exe",
          "size_bytes": 32018512
        },
        {
          "path": "C:\\SierraChart\\TradeOrdersList.data",
          "size_bytes": 32
        },
        {
          "path": "C:\\SierraChart\\TradePositions.data",
          "size_bytes": 32
        },
        {
          "path": "C:\\SierraChart\\Username.txt",
          "size_bytes": 6
        },
        {
          "path": "C:\\SierraChart\\VersionNumber.txt",
          "size_bytes": 6
        },
        {
          "path": "C:\\SierraChart\\ACS_Source\\ACSILCustomChartBars.h",
          "size_bytes": 6834
        },
        {
          "path": "C:\\SierraChart\\ACS_Source\\ACSILCustomChartBars_Example.cpp",
          "size_bytes": 16178
        },
        {
          "path": "C:\\SierraChart\\ACS_Source\\ACSILDepthBars.h",
          "size_bytes": 13614
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\SierraChart\\Data\\6AM26-CME.scid",
          "size_bytes": 81586376
        },
        {
          "path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
          "size_bytes": 64829136
        },
        {
          "path": "C:\\SierraChart\\Data\\6CM26-CME.scid",
          "size_bytes": 48515496
        },
        {
          "path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
          "size_bytes": 160352976
        },
        {
          "path": "C:\\SierraChart\\Data\\6JM26-CME.scid",
          "size_bytes": 122273856
        },
        {
          "path": "C:\\SierraChart\\Data\\6SM26-CME.scid",
          "size_bytes": 32879096
        },
        {
          "path": "C:\\SierraChart\\Data\\AAPL.scid",
          "size_bytes": 3266607856
        },
        {
          "path": "C:\\SierraChart\\Data\\AMZN-NQTV.scid",
          "size_bytes": 767299736
        },
        {
          "path": "C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid",
          "size_bytes": 650097256
        },
        {
          "path": "C:\\SierraChart\\Data\\CLM26-NYMEX.scid",
          "size_bytes": 255670496
        },
        {
          "path": "C:\\SierraChart\\Data\\ESM26-CME.scid",
          "size_bytes": 1878801976
        },
        {
          "path": "C:\\SierraChart\\Data\\EURUSD.scid",
          "size_bytes": 1009038416
        },
        {
          "path": "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
          "size_bytes": 155486896
        },
        {
          "path": "C:\\SierraChart\\Data\\M2KM26-CME.scid",
          "size_bytes": 171330576
        },
        {
          "path": "C:\\SierraChart\\Data\\MCLM26-NYMEX.scid",
          "size_bytes": 194206936
        },
        {
          "path": "C:\\SierraChart\\Data\\MESM26-CME.scid",
          "size_bytes": 1368440256
        },
        {
          "path": "C:\\SierraChart\\Data\\MESU25-CME.scid",
          "size_bytes": 56
        },
        {
          "path": "C:\\SierraChart\\Data\\MGCM26-COMEX.scid",
          "size_bytes": 456427976
        },
        {
          "path": "C:\\SierraChart\\Data\\MNQM26-CME.scid",
          "size_bytes": 2777206376
        },
        {
          "path": "C:\\SierraChart\\Data\\MYMM26-CBOT.scid",
          "size_bytes": 247983296
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 40074558998,
      "truncated": false
    },
    {
      "dir_count": 9,
      "errors": [],
      "exists": true,
      "extension_counts": {
        ".bat": 1,
        ".csv": 3,
        ".ini": 1,
        ".json": 7,
        ".local": 1,
        ".log": 10,
        ".md": 62,
        ".pdf": 2,
        ".png": 5,
        ".ps1": 1,
        ".py": 13,
        ".sh": 3,
        ".toml": 1,
        ".txt": 2,
        ".xlsx": 2,
        "[no_ext]": 4
      },
      "file_count": 118,
      "hash_deferral_records": [
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        },
        {
          "exact_rehash_procedure": "Run a future source-control lane to compute sha256 over C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx read-only, record hash/size/mtime, and keep the raw file uncommitted.",
          "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
          "reason": "Raw/heavy market data blob is not committed or copied by this route.",
          "suffix": ".xlsx"
        }
      ],
      "hashed_control_samples": [
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
          "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
          "size_bytes": 7472
        },
        {
          "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
          "size_bytes": 9245
        }
      ],
      "is_dir": true,
      "label": "documents_targeted_shallow",
      "manifest_control_candidate_count": 2,
      "market_data_like_count": 5,
      "max_depth": 1,
      "no_raw_market_blob_content_copied": true,
      "parser_candidate_count": 0,
      "path": "C:\\Users\\MSI\\Documents",
      "raw_market_blob_count": 2,
      "recursive": true,
      "sample_manifest_control_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\COMPREHENSIVE_STATUS_REPORT.md",
          "size_bytes": 7472
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ORCHESTRATION_STATUS_REPORT_20260407.md",
          "size_bytes": 9245
        }
      ],
      "sample_other_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\desktop.ini",
          "size_bytes": 402
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ETF_Flows_March_2026.csv",
          "size_bytes": 17873
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\GTOS_Tokyo_KZ_Wake_Launch.ps1",
          "size_bytes": 820
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.DS_Store",
          "size_bytes": 24580
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.env",
          "size_bytes": 491
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.env.local",
          "size_bytes": 420
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.gitattributes",
          "size_bytes": 939
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.gitignore",
          "size_bytes": 8494
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\AGENTS.md",
          "size_bytes": 36948
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\asba.txt",
          "size_bytes": 354
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\autocorrelation_baselines.md",
          "size_bytes": 2055
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\batch_backtest.log",
          "size_bytes": 0
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CEO_DIRECTIVE_COMPLETION_REPORT.md",
          "size_bytes": 1662
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CLAUDE.md",
          "size_bytes": 33549
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\CORRECTED_INTELLIGENCE_BRIEF_APRIL7.md",
          "size_bytes": 5032
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\DATA_VERIFICATION_MATRIX.md",
          "size_bytes": 11668
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\decomposition_raw_results.json",
          "size_bytes": 9167
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\decomposition_real_mso_test.md",
          "size_bytes": 6466
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\defaults_and_tests_audit.md",
          "size_bytes": 11784
        }
      ],
      "sample_parser_files": [],
      "sample_raw_or_heavy_files": [
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\ETF_Flows_March_2026.xlsx",
          "size_bytes": 1388474
        },
        {
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\GDT_Tables_Q126_EN.xlsx",
          "size_bytes": 249270
        }
      ],
      "scan_policy": "metadata_only_no_content_copy",
      "status": "ROOT_PRESENT_SCANNED_METADATA_ONLY",
      "total_bytes": 16097105,
      "truncated": false
    }
  ],
  "schema_version": "g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_v1",
  "source_control_closure_status": "CLOSED_WITH_METADATA_COVERAGE_AND_HASH_DEFERRALS",
  "total_file_count_metadata_only": 118563,
  "total_market_data_like_count_metadata_only": 6611,
  "total_raw_market_blob_count_metadata_only": 736,
  "validation_safe": false
}
```
