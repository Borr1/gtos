# G12 Next-Lane Recommendations - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

| Priority | Lane | Action | Depends on |
| --- | --- | --- | --- |
| P0 | OTB1_REBUILD_INPUT_ONLY_LIFECYCLE_PROJECTION | Drop path_label and all R/path/touch result keys before source hashing; write sanitized source-row hash and count raw rows versus unique duplicate_group_id. | No outcome opening; local source projection only. |
| P0 | OTB2_REBUILD_INPUT_ONLY_PATH_PACKET | Create a source projection for candidate_ltf_path_order that excludes path_order_label and touch/result times, then bind path windows to coverage-valid M1/OHLC or explicit path-order input rows. | No result-bearing event logs; no Databento/API call. |
| P1 | G0_G12_OTB3_SIDECAR_REVIEW | Apply or reject OTB3 proposed no-leak/source-ref rewrites through an owner-approved registry patch, preserving validation_safe=false and outcome_review_opened=false. | Owner/G0 registry patch lane, not outcome testing. |
| P1 | G12_REAUDIT_AFTER_REBUILD | Run the same packet/source/no-leak audit before any quarantine/result lane opens. | Rebuilt packets with machine-checkable sanitized source hashes. |
