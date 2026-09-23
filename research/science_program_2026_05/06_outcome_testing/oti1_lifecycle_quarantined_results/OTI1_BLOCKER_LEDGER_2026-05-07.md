# OTI1 Blocker Ledger - 2026-05-07

**Lane:** `OTI1`  
**Artifact type:** `blocker_ledger`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

| Packet | Blocker | Claim blocked | Lifecycle counts blocked | Reason |
| --- | --- | --- | --- | --- |
| OTG0-PKT-016 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | friction fields have a residual G12 question; no packet-bound as-of friction source is proven |
| OTG0-PKT-025 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | realized-vol and vol-of-vol source is not packet-bound for source-complete volatility claims |
| OTG0-PKT-045 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | footprint/absorption source contract and as-of proof are not packet-bound |
| OTG0-PKT-055 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | news event-window matcher/parser/no-lookahead fixtures are not cleared |
| OTG0-PKT-059 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | macro-attention and G5/G7 interaction source labels are not packet-bound |
| OTG0-PKT-071 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | FOMC parser, stale-source tests, event windows, and no-lookahead checks are not cleared |
| OTG0-PKT-079 | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER | covariate_or_source_complete_claim | False | Cboe publication/as-of, parser/cache hashes, legal review, and no-lookahead tests remain unresolved |
| portfolio | VALIDATION_STATS_NOT_COMPUTABLE_NO_NULL_ALT_RETURN_SERIES_OR_VARIANTS | validation_statistics | False | raw p, DSR, and PBO are not computable for this quarantined descriptive lifecycle lane |
| portfolio | NO_PROMOTION_VERDICT_PRESERVED | promotion_or_validation_safe_claim | False | OTI1 creates discovery/quarantine artifacts only and does not edit registries or source validation flags |
