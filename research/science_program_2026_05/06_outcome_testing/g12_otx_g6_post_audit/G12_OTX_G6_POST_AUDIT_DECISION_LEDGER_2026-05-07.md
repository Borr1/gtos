# G12 Otx G6 Post Audit Decision Ledger

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "artifact_family": "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER",
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "packet_decisions": [
    {
      "accepted_evidence": {
        "otb6_generic_comparator_ready_rows": 80,
        "otb6_unique_matched_control_groups": 20,
        "otx_ordered_tick_path_ready_rows": 79,
        "otx_quote_ready_rows": 76
      },
      "blocking_evidence": {
        "local_artifact_status": "NO_VALID_ASOF_MECHANICAL_OB_SOURCE_ROW_FOUND",
        "required_fields": [
          "candidate_id",
          "setup_id",
          "packet_id",
          "experiment_id",
          "symbol",
          "decision_asof_utc",
          "source_capture_utc",
          "source_path",
          "source_sha256",
          "row_hash",
          "feature_asof_utc_lte_decision_asof_utc",
          "duplicate_group_id",
          "no_result_fields_assertion",
          "market_state_source_path",
          "market_state_source_sha256",
          "market_state_row_hash",
          "timeframe",
          "ob_id",
          "ob_low",
          "ob_high",
          "ob_mid",
          "ob_created_utc",
          "impulse_bos_utc",
          "mitigation_state",
          "touch_sequence",
          "poi_price_level",
          "selected_ob_reason",
          "matched_control_group_id"
        ],
        "required_schema": "mechanical_ob_bounds_asof_v1"
      },
      "decision_reason": "G12 accepts OTX's blocker. External quote ticks can prove decision quotes and path availability, and OTB6 proved the matched generic comparator, but no approved local source proves the selected H1 mechanical OB id/bounds/source-row/touch sequence required to compare OB versus generic retrace.",
      "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
      "future_unblocker": "Prospective mechanical_ob_bounds_asof_v1 capture with market_state source path/hash, row hash, H1 OB id, ob_low/high/mid, OB creation UTC, impulse BOS UTC, mitigation state, and touch_sequence for every row.",
      "packet_id": "OTG0-PKT-060",
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS"
    },
    {
      "accepted_evidence": {
        "absolute_tick_file": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
        "absolute_tick_file_min_ts_utc": "2026-05-06T17:16:17.131000+00:00",
        "blocked_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
        "decision_quote_window_rows": 0,
        "ordered_tick_path_ready_rows": 50,
        "quote_ready_rows": 50
      },
      "blocking_evidence": {
        "decision_quote_packet": {
          "decision_asof_utc": "2026-05-06T07:15:00Z",
          "missing_tick_files": [],
          "quote_status": "DECISION_QUOTE_NOT_FOUND_WITHIN_5M",
          "tick_source_files": [
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
          ]
        },
        "missing_window": "XAUUSD 2026-05-06T07:10:00Z through 2026-05-06T11:15:00Z for decision quote plus fixed OTX path horizon",
        "ordered_tick_path_packet": {
          "missing_tick_files": [],
          "ordered_path_source_id": "61d9086fe8a5a85e9a265e819e51c226",
          "path_end_utc": "2026-05-06T11:15:00Z",
          "path_first_timestamp_utc": null,
          "path_horizon_source": "otx_fixed_4h_path_horizon_for_reaudit_only",
          "path_last_timestamp_utc": null,
          "path_row_count": 0,
          "path_row_count_status": "EXACT_FILTERED_TICK_COUNT",
          "path_source_files": [
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
          ],
          "path_source_sha256": {
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439"
          },
          "path_source_type": "tick_parquet_quote_stream",
          "path_start_utc": "2026-05-06T07:15:00Z",
          "path_status": "ORDERED_TICK_PATH_EMPTY_OR_MISSING"
        }
      },
      "decision_reason": "G12 accepts OTX's partial coverage blocker after inspecting the absolute main tick source. 50/51 rows have quotes and ordered paths; the one XAUUSD 2026-05-06 07:15 UTC row has no decision quote and no ordered path in approved local ticks.",
      "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
      "future_unblocker": "Recover or recapture XAUUSD ticks covering at least 2026-05-06 07:10-11:15 UTC, hash the source parquet, and rebuild continuation_no_retrace_decision_price_path_v1 before any CNR result lane.",
      "packet_id": "OTG0-PKT-061",
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE"
    },
    {
      "accepted_evidence": {
        "countable_discovery_rows": 9,
        "duplicate_policy": "one countable primary unique breakout per duplicate_breakout_key_otx",
        "mean_synthetic_r_resolved_only": -0.5,
        "raw_rows": 86,
        "resolved_synthetic_r_rows": 5
      },
      "blocked_from_promotion_by": [
        "sample floor not met",
        "DSR/PBO/effective-N not computable",
        "same-dataset discovery quarantine",
        "synthetic path-R is not broker actual-R"
      ],
      "decision_reason": "G12 accepts OTX's OTI4B ledger only as tick-recomputed quarantined discovery evidence. It is below sample floor, uses synthetic path-R only, keeps broker actual-R closed, and has explicit duplicate/row exclusions.",
      "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
      "future_unblocker": "Only a future source-complete opening-drive lane with >=200 unique breakout groups and a separate G12 result audit may make any validation-style claim.",
      "packet_id": "OTG0-PKT-062",
      "row_exclusion_evidence": {
        "NOT_COUNTABLE_OPENING_DRIVE_FILTER_FAILED": 77
      },
      "terminal_g12_decision": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS"
    },
    {
      "blocked_from_promotion_by": [
        "future lane not yet run",
        "synthetic/path result labels still closed",
        "sample floor and DSR/PBO/effective-N not yet established"
      ],
      "decision_reason": "G12 accepts the OTX CUSUM/changepoint proposal as an input-only future result-lane substrate for the 81 source-ready rows only. Five rows are excluded because predecision M1/tick coverage is insufficient.",
      "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
      "frozen_allowed_subset": {
        "excluded_record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00"
        ],
        "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
        "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
        "required_status": "PREREGISTERED_TICK_CUSUM_FEATURE_READY",
        "source_ready_rows": 81
      },
      "future_unblocker": "Run a separate quarantined CUSUM result audit using only the frozen 81-row source-ready subset, preserving duplicate-group policy and no broker actual-R.",
      "packet_id": "OTG0-PKT-063",
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    },
    {
      "blocked_from_promotion_by": [
        "only three current source-ready rows",
        "sample floor 150 XAU OB-retouch rows not met",
        "future synthetic/path result labels still closed"
      ],
      "decision_reason": "G12 accepts the OTX sweep/round-number proposal as an input-only future result-lane substrate for the three source-ready XAU rows only. Four rows are excluded because decision quote/predecision tick coverage is absent or not as-of complete.",
      "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
      "frozen_allowed_subset": {
        "accepted_record_ids": [
          "OTG0-PKT-066|XAUUSD_2026-05-04T07:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-05T08:00:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-05T08:15:00+00:00"
        ],
        "excluded_record_ids": [
          "OTG0-PKT-066|XAUUSD_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-03T16:30:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-06T07:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-06T08:00:00+00:00"
        ],
        "required_feature_asof_lte_decision": true,
        "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
        "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
        "required_sweep_status": "STRUCTURED_SWEEP_FIELDS_READY",
        "sample_floor": 150,
        "source_ready_rows": 3
      },
      "future_unblocker": "Collect or rebuild enough source-ready XAU OB-zone/round-number sweep rows to reach the 150-row floor before scoring beyond parser dry-run.",
      "packet_id": "OTG0-PKT-066",
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "scope": "G12 post-audit of OTX G6 tick-aware resolution",
  "summary_counts": {
    "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS": 1,
    "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS": 2,
    "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS": 1,
    "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE": 1
  },
  "validation_safe": false
}
```
